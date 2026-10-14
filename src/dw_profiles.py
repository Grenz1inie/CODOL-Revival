"""Opaque CODOL public profiles; do not invent or edit DDL field offsets.

Wire evidence: dwProfile::deserialize at 0x006d7740 and bdProfileInfo base
0x00a5a370, target e3823fd6... . The saved 8/3 body starts after the user ID;
8/1 results prepend that typed ID. Final 00 is the request terminator.
"""
import struct
import zlib


class ProfileError(ValueError):
    pass


def validate_profile(wire):
    if (len(wire) < 22 or wire[0] != 8 or wire[5] != 8 or wire[10] != 8
            or wire[15:17] != b'\x13\x08' or wire[-1] != 0):
        raise ProfileError('invalid CODOL public profile header/terminator')
    compressed, format_marker, checksum, length = (
        struct.unpack_from('<I', wire, offset)[0] for offset in (1, 6, 11, 17))
    if compressed != 1 or format_marker != 1:
        raise ProfileError('only the observed compressed profile header (1, 1) is supported')
    if 21 + length > len(wire) - 1:
        raise ProfileError('truncated public profile blob')
    try:
        raw = zlib.decompress(wire[21:21 + length])
    except zlib.error as error:
        raise ProfileError('invalid profile zlib data') from error
    if len(raw) != 32768:
        raise ProfileError('profile must expand to 32768 bytes')
    if checksum != struct.unpack_from('<I', raw)[0] or checksum != zlib.crc32(raw[4:]):
        raise ProfileError('profile CRC32 mismatch')
    return raw


class ProfileStore:
    def __init__(self, directory):
        self.directory = directory

    def save(self, user_id, wire):
        validate_profile(wire)
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f'{user_id:016x}.bin'
        temporary = path.with_suffix('.tmp')
        temporary.write_bytes(wire)
        temporary.replace(path)

    def load(self, user_id):
        path = self.directory / f'{user_id:016x}.bin'
        if not path.exists():
            return None
        wire = path.read_bytes()
        validate_profile(wire)
        return b'\x0a' + struct.pack('<Q', user_id) + wire[:-1]
