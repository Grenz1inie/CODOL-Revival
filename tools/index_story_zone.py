"""Bounded readers for FF427 directories, netconststrings, and rawfile assets.

REA: directory 0x484750; asset loaders 0x495d60 and 0x494d00.
Preserve serialized order: a per-map string list is not the full runtime registry.
"""
import struct
import zlib


def read_baselines(data):
    """Client 0x5849f0 accepts at most 700 states of 0x110 bytes.

    Keep disk state bytes unchanged; runtime origin encoding is a separate step.
    Record ordinal and entity number are distinct, as consumed by 0x46c250.
    """
    if data[:8] != b'IWCB000\x01' or (len(data) - 8) % 272 or len(data) > 190408:
        raise ValueError('baseline header/length mismatch')
    rows = []
    for offset in range(8, len(data), 272):
        entity_id, entity_type = struct.unpack_from('<ii', data, offset)
        if not 0 <= entity_id <= 2048 or entity_type < 0:
            raise ValueError('baseline entity range mismatch')
        rows.append({'index': len(rows), 'entity_id': entity_id, 'entity_type': entity_type,
                     'state': bytes(data[offset:offset + 272])})
    return rows


def read_assets(zone):
    if len(zone) < 56 or struct.unpack_from('<I', zone)[0] != len(zone) - 40:
        raise ValueError('zone length mismatch')
    strings, _, count, _ = struct.unpack_from('<4I', zone, 40)
    cursor = 56 + strings * 4
    if cursor > len(zone):
        raise ValueError('string directory truncated')
    for i in range(strings):
        pointer = struct.unpack_from('<I', zone, 56 + i * 4)[0]
        if pointer == 0xffffffff:
            cursor = zone.index(b'\0', cursor) + 1
        elif pointer != 0:
            raise ValueError('unsupported serialized string pointer')
    end = cursor + count * 16
    if end > len(zone):
        raise ValueError('asset directory truncated')
    assets = []
    for index in range(count):
        kind, offset, pointer, size = struct.unpack_from('<4I', zone, cursor + index * 16)
        # Client intentionally drops aipaths/glass/vehicle-track pointers; their
        # serialized directory entries have zero payload (0x49a320).
        omitted = kind in (14, 17, 18) and size == 0
        # 0x48aad0 and equivalent pointer loaders resolve block-3 aliases without
        # consuming a new payload. Do not mistake them for missing asset bytes.
        shared = size == 0 and (pointer - 1) >> 28 == 3
        if offset + 40 != end or end + size > len(zone) or (not omitted and not shared and pointer not in (0, 0xffffffff, 0xfffffffe)):
            raise ValueError('asset range/pointer mismatch')
        assets.append((kind, bytes(zone[end:end + size])))
        end += size
    if end != len(zone):
        raise ValueError('unaccounted zone bytes')
    return assets


def read_ncs(data):
    if len(data) < 20:
        raise ValueError('truncated NCS')
    name_ptr, kind, source, count, strings_ptr = struct.unpack_from('<5I', data)
    if name_ptr != 0xffffffff or strings_ptr != (0xffffffff if count else 0):
        raise ValueError('unsupported NCS pointer')
    end = data.index(b'\0', 20)
    name = data[20:end].decode('ascii')
    start = end + 1
    cursor = start + count * 4
    if cursor > len(data):
        raise ValueError('truncated NCS pointer array')
    strings = []
    for index in range(count):
        if struct.unpack_from('<I', data, start + index * 4)[0] != 0xffffffff:
            raise ValueError('unsupported NCS string reference')
        end = data.index(b'\0', cursor)
        strings.append(data[cursor:end].decode('ascii'))
        cursor = end + 1
    if cursor != len(data):
        raise ValueError('unaccounted NCS bytes')
    return {'name': name, 'type': kind, 'source': source, 'strings': strings}


def read_rawfile(data):
    if len(data) < 16:
        raise ValueError('truncated rawfile')
    name_ptr, packed_size, size, buffer_ptr = struct.unpack_from('<4I', data)
    if name_ptr != 0xffffffff or buffer_ptr != 0xffffffff:
        raise ValueError('unsupported rawfile pointer')
    end = data.index(b'\0', 16)
    name = data[16:end].decode('ascii')
    payload = data[end + 1:]
    if packed_size:
        if len(payload) != packed_size:
            raise ValueError('rawfile packed length mismatch')
        stream = zlib.decompressobj()
        payload = stream.decompress(payload, size + 1)
        if not stream.eof or stream.unused_data or stream.unconsumed_tail:
            raise ValueError('rawfile compressed stream mismatch')
    elif len(payload) == size + 1 and payload[-1:] == b'\0':
        payload = payload[:-1]
    if len(payload) != size:
        raise ValueError('rawfile decoded length mismatch')
    return name, payload
