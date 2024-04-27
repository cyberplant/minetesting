# taken from https://gist.github.com/NeatMonster/c06c61ba4114a2b31418a364341c26c0

from rich import print
from struct import pack, unpack, calcsize

def lr_pack(fields_to_pack):
    resp = []
    buf = []
    for packing_type, field_name, field in fields_to_pack:
        packed = pack(">" + packing_type, field)
    
        resp.append((field_name, packed))
        buf.append(packed)
    #print(resp)
    print(str(hexdump("Sent>", *resp)))
    return b"".join(buf)

def lr_unpack(packing_types, data):
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




class hexdump:
    def __init__(self, header="", *fields):
        #print(fields)
        print("------------------------")
        self.header = header
        start_pos = 0
        self.color_list = []
        self.buf = b""
        for c, f in enumerate(fields, 1):
            for i in range(0, len(f[1])):
                self.color_list.append(c)
            data = f[1]
            print(f"[header][color({c})]{f[0]:25} : {data}", end=" ")
            if len(f) > 2:
                print(f[2])
            else:
                print()
            self.buf += f[1]
        print("Buf size:", len(self.buf))

    def color(self, pos):
        return self.color_list[pos]

    def get_hexas(self, ba, i):
        hexas = " ".join(("[color({c})]{:02x}[/color({c})]".format(x, c=self.color(p)) for p, x in enumerate(ba, i)))
        for n in range(len(ba), 16):
            hexas += "   "
        return hexas

    def get_chars(self, ba, i):
        resp = []
        for p, b in enumerate(ba, i):
            if 32 <= b < 127:
                char = chr(b)
            else:
                char = "."

            resp.append(f"[color({self.color(p)})]{char}")
        for n in range(len(resp), 16):
            resp.append(" ")
        return "".join(resp)

    def __iter__(self):
        last_bs, last_line = None, None

        for i in range(0, len(self.buf), 16):
            #print(i)
            bs = bytearray(self.buf[i : i + 16])
            line = "[cyan]{}[white]{:08x}  {:80}   |{:16}|".format(
                self.header,
                i,
                self.get_hexas(bs, i),
                self.get_chars(bs, i)
            )
            if bs != last_bs or line != last_line:
                yield line
            last_bs, last_line = bs, line

    def __str__(self):
        return "\n".join(self)

    def __repr__(self):
        return "\n".join(self)
