"""Read the 3.19 asset database and current clipMap through a bounded reader."""
import struct


class LoadedResources:
    def __init__(self, read):
        self.reader = read

    def read(self, address, count):
        if not address or not 0 < count <= 16 * 1024 * 1024:
            raise ValueError('Invalid resource read bounds')
        data = self.reader(address, count)
        if len(data) != count:
            raise ValueError('Incomplete resource read')
        return data

    def words(self, address, count=1):
        return struct.unpack('<' + 'I' * count, self.read(address, count * 4))

    def string(self, address):
        value = self.read(address, 256)
        if b'\0' not in value:
            raise ValueError('Unterminated resource string')
        return value.split(b'\0')[0].decode('gb18030')

    def asset(self, kind, name):
        key = kind
        name = name.lower().replace('\\', '/')
        for value in name.encode('ascii'):
            key = (key * 31 + value) & 0xffffffff
        index = self.words(0x1e2d338 + key % 120000 * 4)[0]
        seen = set()
        while index:
            if not 0 < index < 150000 or index in seen or len(seen) >= 1000:
                raise ValueError('Invalid resource database chain')
            seen.add(index)
            entry = self.words(0x239b120 + index * 28, 7)
            if entry[0] == kind and self.string(self.words(entry[2])[0]).lower() == name:
                return entry[2]
            index = entry[5]
        raise ValueError('Resource not loaded: ' + name)

    def weapons(self):
        names = ['none']
        # The common registration follows code_post_gfx (native source/name sort).
        for label in ('ncs_wep_code_post_gfx_mp', 'ncs_wep_common_mp'):
            _, kind, source, count, pointer = self.words(self.asset(44, label), 5)
            if kind != 13 or source != 0 or not 0 < count < 1700:
                raise ValueError('Invalid weapon registration')
            prior = set(names)
            names.extend(value for p in self.words(pointer, count)
                         if (value := self.string(p)) not in prior)
        return names

    def table(self, name):
        _, columns, rows, pointer = self.words(self.asset(37, name), 4)
        if not 0 < columns <= 128 or not 0 < rows * columns <= 500000:
            raise ValueError('Invalid string table dimensions')
        cells = self.words(pointer, rows * columns * 2)
        return [[self.string(cells[(r * columns + c) * 2]) for c in range(columns)] for r in range(rows)]

    def classes(self):
        definition = self.words(self.asset(39, 'mp/playerdata.def'), 3)[2]
        header = self.words(definition, 16)
        if header[:2] != (233, 1248641861) or header[10:14] != (5, 0, 15767, 3927):
            raise ValueError('Unsupported public player schema')
        offsets = self.words(header[14], header[13])
        fields = {'character': 0, 'lethal': 6, 'tactical': 32, 'primary': 22, 'secondary': 29,
                  'primary_attach': (16, 6), 'secondary_attach': (23, 6), 'perks': (10, 6)}
        classes = []
        for i in range(60):
            base = 1607 + i * 37
            classes.append({k: list(offsets[base+v[0]:base+v[0]+v[1]]) if isinstance(v, tuple)
                            else offsets[base+v] for k, v in fields.items()})
        # Unselected DDL fields may encode bit offsets. Only these typed fields
        # are consumed as bytes by playerdata_classes319.
        for entry in [*classes, {'loadoutVersion': offsets[926]}]:
            for key, value in entry.items():
                width = 2 if key == 'character' else 4
                if any(offset + width > header[12] for offset in (value if isinstance(value, list) else [value])):
                    raise ValueError('Player schema offset exceeds profile')
        return {'classes': classes, 'loadoutVersion': offsets[926]}

    def clipmap(self, map_name):
        header = self.read(0x77e1c00, 256)
        word = lambda offset: struct.unpack_from('<I', header, offset)[0]
        if self.string(word(0)) != f'maps/mp/{map_name}.d3dbsp':
            raise ValueError('Requested collision map is not loaded')
        records = {}

        def block(address, count, stride):
            if not 0 <= count <= 1000000:
                raise ValueError('Invalid collision array size')
            if not count:
                return b''
            data = self.read(address, count * stride)
            records[address] = data
            return data

        block(word(0), 256, 1)
        block(word(0x0c), word(8), 20)
        materials = block(word(0x14), word(0x10), 12)
        count = struct.unpack_from('<H', header, 0x38)[0]
        if not count:
            raise ValueError('Collision map has no brushes')
        brushes = block(word(0x3c), count, 36)
        bounds = block(word(0x40), count, 24)
        block(word(0x44), count, 4)
        for offset, stride in ((0x64, 12), (0x6c, 6), (0x80, 12), (0x88, 32)):
            block(word(offset+4), word(offset), stride)
        ladders = []
        for i in range(count):
            brush = brushes[i*36:(i+1)*36]
            sides_count, sides_pointer = struct.unpack_from('<H2xI', brush)
            sides = block(sides_pointer, sides_count, 8)
            indices = [*struct.unpack_from('<6H', brush, 12),
                       *[struct.unpack_from('<H', sides, s*8+4)[0] for s in range(sides_count)]]
            for material in dict.fromkeys(indices):
                if material >= word(0x10):
                    raise ValueError('Invalid collision material index')
                pointer, flags, _ = struct.unpack_from('<III', materials, material*12)
                if flags & 8:
                    center = struct.unpack_from('<6f', bounds, i*24)
                    ladders.append({'brush': i, 'material': self.string(pointer),
                                    'mins': [center[j]-center[j+3] for j in range(3)],
                                    'maxs': [center[j]+center[j+3] for j in range(3)]})
                    break
        capture = b'CM319\0\0\0' + struct.pack('<I', 0x77e1c00) + header
        return capture + b''.join(struct.pack('<II', address, len(data)) + data
                                 for address, data in records.items()), ladders
