"""CODOL 3.3.3.3 private profile v19, from research/evidence/live-player-schema.json.

Offsets below start at the DDL data, after the four-byte profile CRC.
REA 0x6d7740 reads the same envelope for public and private profiles.
"""
from datetime import datetime, timezone
import struct
import threading
import zlib
from dw_profiles import ProfileError, validate_profile

MAX_LEVEL = 70
MAX_PRESTIGE = 3
DDL_HEADER = (19, 2318499177)
# DDL flags 0x20, in property traversal order. Wire tags: int32=7, float32=13.
EXTENSIONS = (
    (8, 7), (672, 7), (676, 7), (680, 7), (4816, 7), (4820, 7),
    (4824, 7), (4828, 7), (4832, 7), (4836, 7), (4840, 7),
    (4844, 7), (4848, 7), (4852, 7), (4856, 7), (4860, 13),
    (4864, 7), (4868, 7), (4879, 7), (4883, 7), (4887, 7),
    (4891, 7), (4895, 7), (4899, 7), (4903, 7), (4907, 7),
    (4911, 7), (4915, 7), (4919, 7), (4923, 7), (4927, 7),
    (4931, 7), (4935, 7), (4947, 7), (4951, 7), (4955, 13),
)


class PrivateProfileStore:
    def __init__(self, directory, backups):
        self.directory = directory
        self.backups = backups
        self.lock = threading.Lock()

    def _decode(self, wire):
        raw = validate_profile(wire)
        if struct.unpack_from('<II', raw, 4) != DDL_HEADER:
            raise ProfileError('unsupported private profile definition')
        length = struct.unpack_from('<I', wire, 17)[0]
        expected = b''.join(bytes([tag]) + raw[offset + 4:offset + 8] for offset, tag in EXTENSIONS)
        if wire[21 + length:-1] != expected:
            raise ProfileError('private profile extension fields do not match its data')
        return raw

    def load(self, user_id):
        path = self.directory / f'{user_id:016x}.bin'
        if not path.exists():
            return None
        wire = path.read_bytes()
        self._decode(wire)
        return b'\x0a' + struct.pack('<Q', user_id) + wire[:-1]

    def summary(self, user_id):
        result = self.load(user_id)
        if result is None:
            return {}
        raw = self._decode(result[9:] + b'\0')
        prestige, level = struct.unpack_from('<ii', raw, 4883)
        return {'level': level, 'prestige': prestige}

    def save(self, user_id, wire):
        self._decode(wire)
        path = self.directory / f'{user_id:016x}.bin'
        if path.exists():
            self.backups.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            (self.backups / f'{stamp}-{user_id:016x}.bin').write_bytes(path.read_bytes())
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(wire)
        temporary.replace(path)

    def set_progression(self, user_id, level, prestige):
        if type(level) is not int or not 1 <= level <= MAX_LEVEL:
            raise ProfileError('等级必须是 1–70 的整数')
        if type(prestige) is not int or not 0 <= prestige <= MAX_PRESTIGE:
            raise ProfileError('此版本转生次数必须是 0–3 的整数')
        with self.lock:
            current = self.load(user_id)
            if current is None:
                # Client initialization: zero buffer, then DDL version/hash (0x6d7ce0).
                raw = bytearray(32768)
                struct.pack_into('<II', raw, 4, *DDL_HEADER)
                struct.pack_into('<II', raw, 4943, user_id >> 32, user_id & 0xffffffff)
            else:
                raw = bytearray(self._decode(current[9:] + b'\0'))
            struct.pack_into('<i', raw, 4844, 0)  # XP within the selected rank.
            struct.pack_into('<iii', raw, 4883, prestige, level, 4)  # rankTable version 4.
            # Shop compares unlockFlagsNew[1], not rank: REA 0x693160 / 0x4a4c10.
            struct.pack_into('<H', raw, 8297, prestige * 100 + level)
            self._save_raw(user_id, raw)
        return self.summary(user_id)

    def unlock_story(self, user_id):
        with self.lock:
            current = self.load(user_id)
            if current is None:
                raise ProfileError('请先登录游戏，生成私有档案')
            raw = bytearray(self._decode(current[9:] + b'\0'))
            # IsMapUnlocked (REA 0x5b1960) requires >=1. coMapList prerequisites
            # map to unlockFlagsNew[150..159]; live v19 offsets include CRC here.
            for offset in range(8595, 8615, 2):
                value = struct.unpack_from('<H', raw, offset)[0]
                struct.pack_into('<H', raw, offset, max(1, value))
            self._save_raw(user_id, raw)
        return {'story_prerequisites_unlocked': 10}

    def _save_raw(self, user_id, raw):
        checksum = zlib.crc32(raw[4:])
        struct.pack_into('<I', raw, 0, checksum)
        compressed = zlib.compress(raw)
        wire = b''.join(b'\x08' + struct.pack('<I', value) for value in (1, 1, checksum))
        wire += b'\x13\x08' + struct.pack('<I', len(compressed)) + compressed
        wire += b''.join(bytes([tag]) + raw[offset + 4:offset + 8] for offset, tag in EXTENSIONS) + b'\0'
        self.save(user_id, wire)
