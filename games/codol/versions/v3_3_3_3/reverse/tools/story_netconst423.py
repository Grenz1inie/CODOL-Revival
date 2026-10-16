"""Offline NCS registration for the measured 3.3.3.3 client.

REA: 0x585000 sorts tables; 0x584d80 removes prior-table duplicates;
0x584ed0 assigns configstrings and CRC. Layout comes from 0xc57118.
The caller must supply the actual selected tables and registration checksum seed.
This neither supplies a missing runtime seed nor publishes a game server.
"""
import struct
import zlib

# (configstring base, capacity, reserved prefix), 21 records from the client.
LAYOUT = (
    (2051, 1024, 1), (4355, 1024, 1), (3075, 32, 1), (3619, 400, 1),
    (952, 1023, 1), (7058, 0, 0), (3107, 512, 1), (4275, 16, 1),
    (4291, 64, 0), (5379, 64, 1), (6351, 16, 1), (6367, 16, 1),
    (2047, 4, 1), (5443, 900, 1), (856, 96, 0), (7058, 0, 0),
    (6416, 128, 1), (6343, 8, 1), (24, 320, 0), (344, 320, 0),
    (7058, 0, 0),
)


def _text(value):
    # Current exports contain ASCII identifiers. Do not guess an encoding for
    # an unknown export: CRC and the client's bytewise comparison depend on it.
    if not isinstance(value, str) or '\0' in value or not value.isascii():
        raise ValueError('NCS identifier must be NUL-free ASCII')
    return value


def read_registration(read, image_base):
    """Bounded read callback from an already verified process; no process writes.

    0x5855d0 computes the seed over network-dvar names in registration order.
    0x5857b0 admits at most 266 pointers; flag 8 selects the codinfo subset.
    """
    def word(va):
        return struct.unpack('<I', read(image_base + va - 0x400000, 4))[0]
    count, seed = word(0x2dfaba4), word(0x2df9d38)
    if not 0 < count <= 266:
        raise ValueError('Unexpected network registration count')
    pointers = struct.unpack('<' + 'I' * count, read(image_base + 0x2dfaba8 - 0x400000, count * 4))
    names, codinfo = [], []
    for pointer in pointers:
        # These two pointers were read from the process and are already relocated.
        name_pointer, flags = struct.unpack('<II', read(pointer, 8))
        raw = read(name_pointer, 128)
        if b'\0' not in raw or not raw[0]:
            raise ValueError('Unterminated or empty network registration name')
        name = _text(raw.split(b'\0', 1)[0].decode('ascii'))
        names.append(name)
        if flags & 8:
            codinfo.append(name)
    checksum = zlib.crc32(''.join(names).encode('ascii'))
    if checksum != seed or word(0x2dfaba4) != count or word(0x2df9d38) != seed:
        raise ValueError('Network registration checksum changed or does not match names')
    return dict(names=names, codinfo_names=codinfo, checksum_seed=seed)


def build_registry(tables, *, checksum_seed, language='chi'):
    if type(checksum_seed) is not int or not 0 <= checksum_seed <= 0xffffffff:
        raise ValueError('A verified uint32 checksum seed is required')
    _text(language)
    kinds = {i: dict(base=b, capacity=c, reserved=r, strings=[], configstrings=[])
             for i, (b, c, r) in enumerate(LAYOUT)}
    names = set()
    for table in tables:
        name = _text(table['name'])
        if not name or name in names:
            raise ValueError('Duplicate or empty NCS table name; select mounted definitions first')
        names.add(name)
        if table['strings'] and not 0 <= table['type'] < len(LAYOUT):
            raise ValueError('Unsupported NCS kind')
        for value in table['strings']:
            _text(value)
    # 0x585045/0x585071 test the language prefix at name+8, after length > 12.
    order = sorted(tables, key=lambda t: (t['source'], t['type'],
                   len(t['name']) > 12 and t['name'][8:].lower().startswith(language.lower() + '_'),
                   t['name']))
    checksum = checksum_seed
    for table in order:
        if not table['strings'] or table['type'] == 15:
            continue
        dest = kinds[table['type']]
        previous = set(dest['strings'])
        # Dedup only against earlier tables. Repetitions within this table stay.
        added = [value for value in table['strings'] if value not in previous]
        count = len(dest['strings'])
        if dest['base'] != 7058:
            if count + len(added) > dest['capacity'] - dest['reserved']:
                raise ValueError(f"NCS kind {table['type']} exceeds current-client capacity")
            start = dest['base'] + dest['reserved'] + count
            dest['configstrings'].extend(range(start, start + len(added)))
        dest['strings'].extend(added)
        for value in added:
            checksum = zlib.crc32(value.encode('ascii'), checksum)
    return dict(checksum_seed=checksum_seed, checksum=checksum, kinds=kinds,
                table_order=[table['name'] for table in order])
