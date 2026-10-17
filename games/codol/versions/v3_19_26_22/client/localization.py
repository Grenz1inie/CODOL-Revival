"""Rebuild the established English resources from text and original game data."""
from bisect import bisect_right
import hashlib
import struct
import zlib

from cryptography.hazmat.primitives.asymmetric import padding
from .fastfile import crypt

ARCHIVE_SHA256 = 'c3a561e41ca05b9c0ba7f8a3f8fd9235784e827cbb323e349e633f182dbf512d'


def pointer_positions(kind, row, material_positions=()):
    if kind == 27:
        return (0, 4)
    if kind == 37:
        name, columns, rows, cells = struct.unpack_from('<4I', row)
        if name != 0xffffffff or cells != 0xffffffff:
            raise ValueError('Unsupported translated string table')
        start = row.index(b'\0', 16) + 1
        return range(start, start + rows * columns * 8, 8)
    return material_positions


def translate_zone(original, spec):
    if hashlib.sha256(original).hexdigest() != spec['source']:
        raise ValueError('English source zone hash mismatch')
    count = struct.unpack_from('<I', original, 48)[0]
    result = bytearray(original[:56+count*16])
    thresholds = [value for value, _ in spec['pointer_deltas']]
    delta = 0
    for i in range(count):
        kind, offset, pointer, size = struct.unpack_from('<4I', original, 56+i*16)
        row = bytearray(original[40+offset:40+offset+size])
        for at in pointer_positions(kind, row, spec['material_pointers'].get(str(i), ())):
            value = struct.unpack_from('<I', row, at)[0]
            if 0x30000000 <= value < 0x40000000:
                index = bisect_right(thresholds, value) - 1
                struct.pack_into('<I', row, at, value + spec['pointer_deltas'][index][1])
        if str(i) in spec['strings']:
            if kind != 27 or row[:4] != b'\xff'*4:
                raise ValueError('Translation must replace an inline localization value')
            text = spec['strings'][str(i)].encode('gb18030')
            if b'\0' in text:
                raise ValueError('Translation contains NUL')
            row = row[:8] + text + row[row.index(b'\0', 8):]
        struct.pack_into('<4I', result, 56+i*16, kind, offset+delta, pointer, len(row))
        result.extend(row)
        delta += len(row) - size
    for at in (0, 20):
        struct.pack_into('<I', result, at, struct.unpack_from('<I', original, at)[0] + delta)
    if hashlib.sha256(result).hexdigest() != spec['result']:
        raise ValueError('English result zone hash mismatch')
    return bytes(result)


def unsigned(original, zone, private):
    material = private.decrypt(original[21:277], padding.PKCS1v15())
    data = zlib.compress(zone, 9)
    if len(data) + 277 > len(original):
        raise ValueError('Translated fastfile exceeds original archive entry capacity')
    # 0x483b40 decrypts only the initial 0x40000-byte I/O buffer. Subsequent
    # unsigned reads (0x484880) feed the inflater without another AES operation.
    boundary = 0x40000 - 277
    data = crypt(data[:boundary], material[:24], material[24:]) + data[boundary:]
    return (b'IWffu100' + original[8:277] + data).ljust(len(original), b'\0')


def patch_archive(original, replacements):
    if hashlib.sha256(original).hexdigest() != ARCHIVE_SHA256:
        raise ValueError('Original 3.19 archive hash mismatch')
    table = struct.unpack_from('<Q', original, 0x24)[0]
    count = struct.unpack_from('<I', original, 0x4c)[0]
    if original[:4] != b'nifs' or table != count * 0x4000 or table + (count+1)*16 > len(original):
        raise ValueError('Unsupported IFS block digest table')
    result = bytearray(original)
    changed = set()
    for old, new in replacements:
        position = original.find(old)
        if not old or len(old) != len(new) or position < 0xac or position+len(old) > table or original.find(old, position+1) >= 0:
            raise ValueError('IFS replacement needs one original entry of equal capacity')
        result[position:position+len(old)] = new
        changed.update(range(position//0x4000, (position+len(old)-1)//0x4000+1))
    for block in changed:
        result[table+block*16:table+(block+1)*16] = hashlib.md5(result[block*0x4000:(block+1)*0x4000]).digest()
    result[table+count*16:table+(count+1)*16] = hashlib.md5(result[table:table+count*16]).digest()
    return bytes(result)
