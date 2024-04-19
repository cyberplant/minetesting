"""
Minetest client. Implements the low level protocol and a few commands.

Created by reading the docs at
http://dev.minetest.net/Network_Protocol
and
https://github.com/minetest/minetest/blob/master/src/clientserver.h
"""
import socket
from struct import pack, unpack, calcsize
from binascii import hexlify
from threading import Thread, Semaphore
from queue import Queue
from collections import defaultdict
import math
from hexdump import hexdump

from rich import print

# Packet types.
CONTROL = 0x00
ORIGINAL = 0x01
SPLIT = 0x02
RELIABLE = 0x03

# Types of CONTROL packets.
CONTROLTYPE_ACK = 0x00
CONTROLTYPE_SET_PEER_ID = 0x01
CONTROLTYPE_PING = 0x02
CONTROLTYPE_DISCO = 0x03

# Initial sequence number for RELIABLE-type packets.
SEQNUM_INITIAL = 0xFFDC

# Protocol id.
PROTOCOL_ID = 0x4F457403

# No idea.
SER_FMT_VER_HIGHEST_READ = 0x1A

# Supported protocol versions lifted from official client.
MIN_SUPPORTED_PROTOCOL = 0x25  # 37  As of 2024-04-19
MAX_SUPPORTED_PROTOCOL = 0x2c  # 44  https://github.com/minetest/minetest/blob/master/src/network/networkprotocol.h

# Client -> Server command ids.
from networkprotocol import TOSERVER, TOCLIENT

class MinetestClientProtocol(object):
    """
    Class for exchanging messages with a Minetest server. Automatically
    processes received messages in a separate thread and performs the initial
    handshake when created. Blocks until the handshake is finished.

    TODO: resend unacknowledged messages and process out-of-order packets.
    """
    def __init__(self, host, username, password=''):
        if ':' in host:
            host, port = host.split(':')
            server = (host, int(port))
        else:
            server = (host, 30000)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server = server
        self.seqnum = SEQNUM_INITIAL
        self.peer_id = 0
        self.username = username
        self.password = password

        # Priority channel, not actually implemented in the official server but
        # required for the protocol.
        self.channel = 0
        # Buffer with the messages received, filled by the listener thread.
        self.receive_buffer = Queue()
        # Last sequence number acknowledged by the server.
        self.acked = 0
        # Buffer for SPLIT-type messages, indexed by sequence number.
        self.split_buffers = defaultdict(dict)

        # Send TOSERVER_INIT and start a reliable connection. The order is
        # strange, but imitates the official client.
        self._handshake_start()

        self._start_reliable_connection()

        # Lock until the handshake is completed.
        self.handshake_lock = Semaphore(0)
        # Run listen-and-process asynchronously.
        thread = Thread(target=self._receive_and_process)
        thread.daemon = True
        thread.start()
        self.handshake_lock.acquire()


    def lr_pack(self, fields_to_pack):
        resp = []
        buf = []
        for packing_type, field_name, field in fields_to_pack:
            packed = pack(">" + packing_type, field)
        
            resp.append((field_name, packed))
            buf.append(packed)
        #print(resp)
        print(str(hexdump("Sent>", *resp)))
        return b"".join(buf)

    def lr_unpack(self, packing_types, data):
        resp = []
        to_dump = []
        for packing_type, field_name in packing_types:
            size = calcsize(packing_type)
            data_to_unpack = data[0:size]
            unpacked = unpack(">" + packing_type, data_to_unpack)
            for u in unpacked:
                resp.append(u)
            data = data[size:]
            to_dump.append((field_name, data_to_unpack, unpacked))
        print(str(hexdump("Recv>", *to_dump)))

        return resp


    def _send(self, packet):
        """ Sends a raw packet, containing only the protocol header. """

        data = [
            ("I", "header_Protocol_ID", PROTOCOL_ID), 
            ("H", "header_Peer_ID", self.peer_id), 
            ("B", "header_Channel", self.channel)
        ] + packet

        self.sock.sendto(self.lr_pack(data), self.server)

    def _handshake_start(self):
        """ Sends the first part of the handshake. """
        packet = [
                ("H", "TOSERVER_INIT", TOSERVER["INIT"]), 
                ("B", "SER_FMT_VER_HIGHEST_READ", SER_FMT_VER_HIGHEST_READ),
                ("H", "MIN_SUPPORTED_PROTOCOL", MIN_SUPPORTED_PROTOCOL), 
                ("H", "MAX_SUPPORTED_PROTOCOL", MAX_SUPPORTED_PROTOCOL),
                ("20s", "username", self.username.encode('utf-8')), 
        ]
        #print(str(hexdump("Sent >> ", packet)))
        self.send_command(packet)

    def _handshake_end(self):
        """ Sends the second and last part of the handshake. """
        #self.send_command(pack('>H', TOSERVER_INIT2))
        self.send_command([('H', "TOSERVER_INIT2", TOSERVER["INIT2"])])
        
    def _start_reliable_connection(self):
        """ Starts a reliable connection by sending an empty reliable packet. """
        self.send_command([])

    def disconnect(self):
        """ Closes the connection. """
        # The "disconnect" message is just a RELIABLE without sequence number.
        #self._send(pack('>H', RELIABLE))
        self._send([('H', "RELIABLE", RELIABLE)])

    def _send_reliable(self, message):
        """
        Sends a reliable message. This message can be a packet of another
        type, such as CONTROL or ORIGINAL.
        """
        # packet = pack('>BH', RELIABLE, self.seqnum & 0xFFFF) + message
        packet = [
         ("B", "RELIABLE", RELIABLE),
         ("H", "seqnum", self.seqnum & 0xFFFF)
        ] + message
        self.seqnum += 1
        self._send(packet)

    def send_command(self, message):
        """ Sends a useful message, such as a place or say command. """
        #start = pack('B', ORIGINAL)
        start = [("B", "ORIGINAL", ORIGINAL)]
        self._send_reliable(start + message)

    def _ack(self, seqnum):
        """ Sends an ack for the given sequence number. """
        #self._send(pack('>BBH', CONTROL, CONTROLTYPE_ACK, seqnum))
        self._send([
           ('B', "CONTROL", CONTROL),
           ('B', "CONTROLTYPE_ACK", CONTROLTYPE_ACK),
           ('H', "seqnum", seqnum),
        ])

    def receive_command(self):
        """
        Returns a command message from the server, blocking until one arrives.
        """
        return self.receive_buffer.get()

    def _process_packet(self, packet):
        """
        Processes a packet received. It can be of type
        - CONTROL, used by the protocol to control the connection
        (ack, set_peer_id and ping);
        - RELIABLE in which it requires an ack and contains a further message to
        be processed;
        - ORIGINAL, which designates it's a command and it's put in the receive
        buffer;
        - or SPLIT, used to send large data.
        """
        packet_type, data = packet[0], packet[1:]

        if packet_type == CONTROL:
            if len(data) == 1:
                assert data[0] == CONTROLTYPE_PING
                # Do nothing. PING is sent through a reliable packet, so the
                # response was already sent when we unwrapped it.
                return

            #control_type, value = self.lr_unpack('>BH', data)

            control_type, value = self.lr_unpack([("B", "control_type"), ("H", "value")], data)

            if control_type == CONTROLTYPE_ACK:
                self.acked = value
            elif control_type == CONTROLTYPE_SET_PEER_ID:
                self.peer_id = value
                self._handshake_end()
                self.handshake_lock.release()
        elif packet_type == RELIABLE:
            seqnum, = self.lr_unpack([('H', 'seqnum')], data[:2])
            self._ack(seqnum)
            self._process_packet(data[2:])
        elif packet_type == ORIGINAL:
            self.receive_buffer.put(data)
        elif packet_type == SPLIT:
            header_size = calcsize('>HHH')
            split_header, split_data = data[:header_size], data[header_size:]
            seqnumber, chunk_count, chunk_num = self.lr_unpack([('H', 'seqnumber'), ('H', 'chunk_count'), ('H', 'chunk_num')], split_header)
            self.split_buffers[seqnumber][chunk_num] = split_data
            if chunk_count - 1 in self.split_buffers[seqnumber]:
                complete = []
                try:
                    for i in range(chunk_count):
                        complete.append(self.split_buffers[seqnumber][i])
                except KeyError:
                    # We are missing data, ignore and wait for resend.
                    pass
                self.receive_buffer.put(b''.join(complete))
                del self.split_buffers[seqnumber]
        else:
            raise ValueError('Unknown packet type {}'.format(packet_type))



    def _receive_and_process(self):
        """
        Constantly listens for incoming packets and processes them as required.
        """
        while True:
            packet, origin = self.sock.recvfrom(1024)
            header_size = calcsize('>IHB')
            header, data = packet[:header_size], packet[header_size:]
            # print("Recv   :" + str(hexdump(header, data)))
            protocol, peer_id, channel = self.lr_unpack([('I', 'protocol'), ('H', 'peer_id'), ('B', 'channel')], header)
            print(protocol, PROTOCOL_ID)
            assert protocol == PROTOCOL_ID, 'Unexpected protocol.'
            assert peer_id == 0x01, 'Unexpected peer id, should be 1 got {}'.format(peer_id)
            self._process_packet(data)


class MinetestClient(object):
    """
    Class for sending commands to a remote Minetest server. This creates a
    character in the running world, controlled by the methods exposed in this
    class.
    """
    def __init__(self, server='localhost:30000', username='user', password='', on_message=id):
        """
        Creates a new Minetest Client to send remote commands.

        'server' must be in the format 'host:port' or just 'host'.
        'username' is the name of the character on the world.
        'password' is an optional value used when the server is private.
        'on_message' is a function called whenever a chat message arrives.
        """
        self.protocol = MinetestClientProtocol(server, username, password)

        # We need to constantly listen for server messages to update our
        # position, HP, etc. To avoid blocking the caller we create a new
        # thread to process those messages, and wait until we have a confirmed
        # connection.
        self.access_denied = None
        self.init_lock = Semaphore(0)
        thread = Thread(target=self._receive_and_process)
        thread.daemon = True
        thread.start()
        # Wait until we know our position, otherwise the 'move' method will not
        # work.
        self.init_lock.acquire()

        if self.access_denied is not None:
            raise ValueError('Access denied. Reason: ' + self.access_denied)

        self.on_message = on_message

        # HP is not a critical piece of information for us, so we assume it's full
        # until the server says otherwise.
        self.hp = 20

    def say(self, message):
        """ Sends a global chat message. """
        message = str(message)
        encoded = message.encode('UTF-16BE')
        packet = pack('>HH', TOSERVER["CHAT_MESSAGE"], len(message)) + encoded
        self.protocol.send_command(packet)

    def respawn(self):
        """ Resurrects and teleports the dead character. """
        packet = pack('>H', TOSERVER_RESPAWN)
        self.protocol.send_command(packet)

    def damage(self, amount=20):
        """
        Makes the character damage itself. Amount is measured in half-hearts
        and defaults to a complete suicide.
        """
        packet = pack('>HB', TOSERVER["DAMAGE"], int(amount))
        self.protocol.send_command(packet)

    def move(self, delta_position=(0,0,0), delta_angle=(0,0), key=0x01):
        """ Moves to a position relative to the player. """
        x = self.position[0] + delta_position[0]
        y = self.position[1] + delta_position[1]
        z = self.position[2] + delta_position[2]
        pitch = self.angle[0] + delta_angle[0]
        yaw = self.angle[1] + delta_angle[1]
        self.teleport(position=(x, y, z), angle=(pitch, yaw), key=key)

    def teleport(self, position=None, speed=(0,0,0), angle=None, key=0x01):
        """ Moves to an absolute position. """
        position = position or self.position
        angle = angle or self.angle

        x, y, z = map(lambda k: int(k*1000), position)
        dx, dy, dz = map(lambda k: int(k*100), speed)
        pitch, yaw = map(lambda k: int(k*100), angle)
        packet = pack('>H3i3i2iI', TOSERVER["PLAYERPOS"], x, y, z, dx, dy, dz, pitch, yaw, key)
        self.protocol.send_command(packet)
        self.position = position
        self.angle = angle

    def turn(self, degrees=90):
        """
        Makes the character face a different direction. Amount of degrees can
        be negative.
        """
        new_angle = (self.angle[0], self.angle[1] + degrees)
        self.teleport(angle=new_angle)

    def walk(self, distance=1):
        """
        Moves a number of blocks forward, relative to the direction the
        character is looking.
        """
        dx = distance * math.cos((90 + self.angle[1]) / 180 * math.pi)
        dz = distance * math.sin((90 + self.angle[1]) / 180 * math.pi)
        self.move((dx, 0, dz))

    def disconnect(self):
        """ Disconnects the client, removing the character from the world. """
        self.protocol.disconnect()

    def _receive_and_process(self):
        """
        Receive commands from the server and process them synchronously. Most
        commands are not implemented because we didn't have a need.
        """
        while True:
            packet = self.protocol.receive_command()
            (command_type,), data = self.lr_unpack([('H', command_type)], packet[:2]), packet[2:]

            if command_type == TOCLIENT["INIT"]:
                # No useful info here.
                pass
            elif command_type == TOCLIENT["MOVE_PLAYER"]:
                # x10000, y10000, z10000, pitch1000, yaw1000 = self.lr_unpack('>3i2i', data)
                x10000, y10000, z10000, pitch1000, yaw1000 = self.lr_unpack([
                    ('i', 'x10000'),
                    ('i', 'y10000'),
                    ('i', 'z10000'),
                    ('i', 'pitch1000'),
                    ('i', 'yaw1000'),
                ], data)
                self.position = (x10000/10000, y10000/10000, z10000/10000)
                self.angle = (pitch1000/1000, yaw1000/1000)
                self.init_lock.release()
            elif command_type == TOCLIENT["CHAT_MESSAGE"]:
                length, bin_message = self.lr_unpack([('H', 'length')], data[:2]), data[2:]
                # Length is not matching for some reason.
                #assert len(bin_message) / 2 == length 
                message = bin_message.decode('UTF-16BE')
                self.on_message(message)
            elif command_type == TOCLIENT["DEATHSCREEN"]:
                self.respawn()
            elif command_type == TOCLIENT["HP"]:
                self.hp, = self.lr_unpack([('B', 'hp')], data)
            elif command_type == TOCLIENT["INVENTORY_FORMSPEC"]:
                pass
            elif command_type == TOCLIENT["INVENTORY"]:
                pass
            elif command_type == TOCLIENT["PRIVILEGES"]:
                pass
            elif command_type == TOCLIENT["MOVEMENT"]:
                pass
            elif command_type == TOCLIENT["BREATH"]:
                pass
            elif command_type == TOCLIENT["DETACHED_INVENTORY"]:
                pass
            elif command_type == TOCLIENT["TIME_OF_DAY"]:
                pass
            elif command_type == TOCLIENT["REMOVENODE"]:
                pass
            elif command_type == TOCLIENT["ADDNODE"]:
                pass
            elif command_type == TOCLIENT["PLAY_SOUND"]:
                pass
            elif command_type == TOCLIENT["STOP_SOUND"]:
                pass
            elif command_type == TOCLIENT["NODEDEF"]:
                pass
            elif command_type == TOCLIENT["ANNOUNCE_MEDIA"]:
                pass
            elif command_type == TOCLIENT["ITEMDEF"]:
                pass
            elif command_type == TOCLIENT["ACCESS_DENIED"]:
                length, bin_message = self.lr_unpack([('H', 'length')], data[:2]), data[2:]
                self.access_denied = bin_message.decode('UTF-16BE')
                self.init_lock.release()
            else:
                print('Unknown command type {}.'.format(hex(command_type)))


if __name__ == '__main__':
    import sys
    import time

    args = sys.argv[1:]
    assert len(args) <= 3, 'Too many arguments, expected no more than 3'
    # Load hostname, username and password from the command line arguments.
    # Defaults to localhost:30000, 'user' and empty password (for public
    # servers).
    client = MinetestClient(*args)
    try:
        # Print chat messages received from other players.
        client.on_message = print
        # Send as chat message any line typed in the standard input.
        while not sys.stdin.closed:
            line = sys.stdin.readline().rstrip()
            client.say(line)
    finally:
        client.protocol.disconnect()
