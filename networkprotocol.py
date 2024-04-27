TOCLIENT = {
   "HELLO": 0x02,
   "AUTH_ACCEPT": 0x03,
   "ACCEPT_SUDO_MODE": 0x04,
   "DENY_SUDO_MODE": 0x05,
   "ACCESS_DENIED": 0x0A,
   "BLOCKDATA": 0x20,
   "ADDNODE": 0x21,
   "REMOVENODE": 0x22,
   "INVENTORY": 0x27,
   "TIME_OF_DAY": 0x29,
   "CSM_RESTRICTION_FLAGS": 0x2A,
   "PLAYER_SPEED": 0x2B,
   "MEDIA_PUSH": 0x2C,
   "CHAT_MESSAGE": 0x2F,
   "ACTIVE_OBJECT_REMOVE_ADD": 0x31,
   "ACTIVE_OBJECT_MESSAGES": 0x32,
   "HP": 0x33,
   "MOVE_PLAYER": 0x34,
   "ACCESS_DENIED_LEGACY": 0x35,
   "FOV": 0x36,
   "DEATHSCREEN": 0x37,
   "MEDIA": 0x38,
   "NODEDEF": 0x3a,
   "ANNOUNCE_MEDIA": 0x3c,
   "ITEMDEF": 0x3d,
   "PLAY_SOUND": 0x3f,
   "STOP_SOUND": 0x40,
   "PRIVILEGES": 0x41,
   "INVENTORY_FORMSPEC": 0x42,
   "DETACHED_INVENTORY": 0x43,
   "SHOW_FORMSPEC": 0x44,
   "MOVEMENT": 0x45,
   "SPAWN_PARTICLE": 0x46,
   "ADD_PARTICLESPAWNER": 0x47,
   "HUDADD": 0x49,
   "HUDRM": 0x4a,
   "HUDCHANGE": 0x4b,
   "HUD_SET_FLAGS": 0x4c,
   "HUD_SET_PARAM": 0x4d,
   "BREATH": 0x4e,
   "SET_SKY": 0x4f,
   "OVERRIDE_DAY_NIGHT_RATIO": 0x50,
   "LOCAL_PLAYER_ANIMATIONS": 0x51,
   "EYE_OFFSET": 0x52,
   "DELETE_PARTICLESPAWNER": 0x53,
   "CLOUD_PARAMS": 0x54,
   "FADE_SOUND": 0x55,
   "UPDATE_PLAYER_LIST": 0x56,
   "MODCHANNEL_MSG": 0x57,
   "MODCHANNEL_SIGNAL": 0x58,
   "NODEMETA_CHANGED": 0x59,
   "SET_SUN": 0x5a,
   "SET_MOON": 0x5b,
   "SET_STARS": 0x5c,
   "MOVE_PLAYER_REL": 0x5d,
   "SRP_BYTES_S_B": 0x60,
   "FORMSPEC_PREPEND": 0x61,
   "MINIMAP_MODES": 0x62,
   "SET_LIGHTING": 0x63,
   "NUM_MSG_TYPES": 0x64,
}

TOSERVER = {
   "INIT": 0x02,
   "INIT2": 0x11,
   "MODCHANNEL_JOIN": 0x17,
   "MODCHANNEL_LEAVE": 0x18,
   "MODCHANNEL_MSG": 0x19,
   "PLAYERPOS": 0x23,
   "GOTBLOCKS": 0x24,
   "DELETEDBLOCKS": 0x25,
   "INVENTORY_ACTION": 0x31,
   "CHAT_MESSAGE": 0x32,
   "DAMAGE": 0x35,
   "PLAYERITEM": 0x37,
   "RESPAWN": 0x38,
   "INTERACT": 0x39,
   "REMOVED_SOUNDS": 0x3a,
   "NODEMETA_FIELDS": 0x3b,
   "INVENTORY_FIELDS": 0x3c,
   "REQUEST_MEDIA": 0x40,
   "HAVE_MEDIA": 0x41,
   "CLIENT_READY": 0x43,
   "FIRST_SRP": 0x50,
   "SRP_BYTES_A": 0x51,
   "SRP_BYTES_M": 0x52,
   "UPDATE_CLIENT_INFO": 0x53,
   "NUM_MSG_TYPES": 0x54,
}

AUTH = {
   "MECHANISM_NONE": 0,
   "MECHANISM_LEGACY_PASSWORD": 1 << 0,
   "MECHANISM_SRP": 1 << 1,
   "MECHANISM_FIRST_SRP": 1 << 2,
}

NETPROTO = {
   "COMPRESSION_NONE": 0,
}

CSM = {
   "RF_NONE": 0x00000000,
   "RF_LOAD_CLIENT_MODS": 0x00000001,
   "RF_CHAT_MESSAGES": 0x00000002,
   "RF_READ_ITEMDEFS": 0x00000004,
   "RF_READ_NODEDEFS": 0x00000008,
   "RF_LOOKUP_NODES": 0x00000010,
   "RF_READ_PLAYERINFO": 0x00000020,
   "RF_ALL": 0xFFFFFFFF,
}

