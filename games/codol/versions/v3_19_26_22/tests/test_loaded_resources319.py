import struct
import unittest

from games.codol.versions.v3_19_26_22.client.loaded_resources import LoadedResources
from games.codol.versions.v3_19_26_22.tests.test_resource_tables319 import Memory
from games.codol.versions.v3_19_26_22.tests.test_collision_build319 import clipmap_fixture


def bind(m, kind, name, pointer, index):
    key = kind
    for b in name.lower().replace('\\', '/').encode():
        key = (key * 31 + b) & 0xffffffff
    m.words(0x1e2d338 + key % 120000 * 4, index)
    m.words(0x239b120 + index * 28, kind, 0, pointer, 0, 0, 0, 0)


class LoadedResourcesTests(unittest.TestCase):
    def test_weapon_registration_and_table_come_from_named_assets(self):
        m = Memory()
        for index, (label, names) in enumerate([
            ('ncs_wep_code_post_gfx_mp', ['defaultweapon_mp']),
            ('ncs_wep_common_mp', ['defaultweapon_mp', 'm4_mp'])], 1):
            base = 0x10000000 + index * 0x10000
            bind(m, 44, label, base, index)
            m.words(base, base+0x100, 13, 0, len(names), base+0x200)
            m.put(base+0x100, label.encode()+bytes(256-len(label)))
            m.words(base+0x200, *[base+0x300+i*256 for i in range(len(names))])
            for i, value in enumerate(names):
                m.put(base+0x300+i*256, value.encode()+bytes(256-len(value)))
        r = LoadedResources(m.read)
        self.assertEqual(r.weapons(), ['none', 'defaultweapon_mp', 'm4_mp'])
        label = 'mp/rankTable.csv'
        bind(m, 37, label, 0x20000000, 3)
        m.words(0x20000000, 0x20000100, 2, 1, 0x20000200)
        m.put(0x20000100, label.encode()+bytes(256-len(label)))
        m.words(0x20000200, 0x20000300, 123, 0x20000400, 456)
        m.put(0x20000300, b'70\0'+bytes(253))
        m.put(0x20000400, b'3582550\0'+bytes(248))
        self.assertEqual(r.table(label), [['70', '3582550']])
        m.words(0x20000000, 0x20000100, 100000, 100000, 0x20000200)
        with self.assertRaisesRegex(ValueError, 'table'):
            r.table(label)

    def test_loadout_offsets_require_current_public_schema(self):
        m = Memory()
        label = 'mp/playerdata.def'
        bind(m, 39, label, 0x10000000, 1)
        m.words(0x10000000, 0x10000100, 1, 0x10000200)
        m.put(0x10000100, label.encode()+bytes(256-len(label)))
        header = [233, 1248641861, 0, 0, 8, 0, 40, 0, 0, 0, 5, 0, 15767, 3927, 0x10010000, 0]
        m.words(0x10000200, *header)
        offsets = [i*4 for i in range(3927)]
        m.words(0x10010000, *offsets)
        r = LoadedResources(m.read)
        layout = r.classes()
        self.assertEqual(layout['loadoutVersion'], 926*4)
        self.assertEqual(layout['classes'][0]['primary'], (1607+22)*4)
        self.assertEqual(layout['classes'][-1]['secondary_attach'], [(1607+59*37+23+j)*4 for j in range(6)])
        # Other DDL members encode bit offsets, not byte offsets (live v233 schema).
        offsets[1614] = 0x1a0d0
        m.words(0x10010000, *offsets)
        self.assertEqual(r.classes(), layout)
        offsets[1607+22] = 32763
        m.words(0x10010000, *offsets)
        with self.assertRaisesRegex(ValueError, 'offset'):
            r.classes()
        header[1] ^= 1
        m.words(0x10000200, *header)
        with self.assertRaisesRegex(ValueError, 'schema'):
            r.classes()

    def test_map_capture_contains_only_referenced_geometry_and_ladders(self):
        m = Memory()
        source = clipmap_fixture()
        header = bytearray(source[12:268])
        struct.pack_into('<I', header, 0, 0x30000100)
        struct.pack_into('<II', header, 0x10, 2, 0x30000200)
        m.put(0x77e1c00, header)
        m.put(0x30000100, b'maps/mp/mp_seatown.d3dbsp\0'+bytes(232))
        m.words(0x30000200, 0, 0, 1, 0x30000300, 8, 0x8010000)
        m.put(0x30000300, b'ladder\0'+bytes(249))
        cursor = 268
        while cursor < len(source):
            address, count = struct.unpack_from('<II', source, cursor)
            cursor += 8
            data = bytearray(source[cursor:cursor+count])
            if address == struct.unpack_from('<I', header, 0x3c)[0]:
                struct.pack_into('<H', data, 3*36+12, 1)
            m.put(address, data)
            cursor += count
        result, ladders = LoadedResources(m.read).clipmap('mp_seatown')
        self.assertEqual(result[:12], b'CM319\0\0\0'+struct.pack('<I', 0x77e1c00))
        self.assertLess(len(result), 2000)
        self.assertEqual(ladders, [{'brush': 3, 'material': 'ladder', 'mins': [100., -25., 0.], 'maxs': [101., 25., 70.]}])
        with self.assertRaisesRegex(ValueError, 'map'):
            LoadedResources(m.read).clipmap('mp_nuked')
        # A partial cross-process read must not produce a valid capture.
        with self.assertRaisesRegex(ValueError, 'read'):
            LoadedResources(lambda address, count: m.read(address, count)[:-1]).clipmap('mp_seatown')

    def test_database_cycle_is_rejected(self):
        m = Memory()
        bind(m, 37, 'mp/rankTable.csv', 0x10000000, 1)
        m.words(0x239b120+28, 37, 0, 0x10000000, 0, 0, 1, 0)
        m.words(0x10000000, 0x10000100)
        m.put(0x10000100, b'other\0'+bytes(250))
        with self.assertRaisesRegex(ValueError, 'chain'):
            LoadedResources(m.read).asset(37, 'mp/rankTable.csv')
