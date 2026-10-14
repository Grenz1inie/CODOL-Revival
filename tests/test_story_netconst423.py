"""Current-client registration contract, independent of the 2697 writer."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest
import zlib

import pefile

ROOT = Path(__file__).resolve().parents[1]


def table(name, kind, values, source=0):
    return dict(name=name, type=kind, source=source, strings=values)


class NetConst423Tests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('story_netconst423', ROOT / 'tools/story_netconst423.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_layout_matches_all_21_records_in_current_client(self):
        data = (ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b')
        pe = pefile.PE(data=data)
        offset = pe.get_offset_from_rva(0xc57118 - pe.OPTIONAL_HEADER.ImageBase)
        self.assertEqual(self.module.LAYOUT, tuple(struct.unpack_from('<3I', data, offset + i * 12)
                                                  for i in range(21)))
        language_slot = pe.get_offset_from_rva(0xcdbc1c + 11 * 12 - pe.OPTIONAL_HEADER.ImageBase)
        language_pointer = struct.unpack_from('<I', data, language_slot)[0]
        language_offset = pe.get_offset_from_rva(language_pointer - pe.OPTIONAL_HEADER.ImageBase)
        self.assertEqual(data[language_offset:language_offset + 4], b'chi\0')

    def test_sort_cross_table_dedup_crc_and_input_ownership(self):
        tables = [table('ncs_mdl_chi_alpha', 0, ['a', 'c']),
                  table('ncs_mdl_level', 0, ['a', 'a', 'b']),
                  table('ncs_mat_level', 1, ['x']),
                  table('ncs_fxt_level', 15, ['ignored']),
                  table('ncs_mdl_other', 0, ['b', 'd'], source=1)]
        original = copy.deepcopy(tables)
        result = self.module.build_registry(tables, checksum_seed=0x12345678)
        self.assertEqual(result['kinds'][0]['strings'], ['a', 'a', 'b', 'c', 'd'])
        self.assertEqual(result['kinds'][0]['configstrings'], [2052, 2053, 2054, 2055, 2056])
        self.assertEqual(result['kinds'][15]['strings'], [])
        self.assertEqual(result['checksum'], zlib.crc32(b'aabcxd', 0x12345678))
        self.assertEqual(tables, original)

    def test_reserved_slots_and_new_kind_capacity(self):
        for kind, capacity in ((0, 1023), (8, 64), (13, 899), (17, 7), (18, 320)):
            with self.subTest(kind=kind):
                values = [str(i) for i in range(capacity)]
                result = self.module.build_registry([table('ncs_test', kind, values)], checksum_seed=0)
                self.assertEqual(len(result['kinds'][kind]['strings']), capacity)
                self.assertEqual(result['kinds'][kind]['configstrings'][0],
                                 {0: 2052, 8: 4291, 13: 5444, 17: 6344, 18: 24}[kind])
                with self.assertRaisesRegex(ValueError, 'capacity'):
                    self.module.build_registry([table('ncs_test', kind, values + ['overflow'])], checksum_seed=0)

    def test_invalid_or_unproven_inputs_are_not_silently_accepted(self):
        with self.assertRaises(TypeError):
            self.module.build_registry([])
        invalid = [[table('ncs_bad', 21, ['x'])],
                   [table('ncs_bad', 0, ['x\0y'])],
                   [table('ncs_bad', 0, [None])],
                   [table('same', 0, ['a']), table('same', 0, ['b'])]]
        for tables in invalid:
            with self.subTest(tables=tables), self.assertRaises(ValueError):
                self.module.build_registry(tables, checksum_seed=0)
        for seed in (-1, 0x100000000, None):
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                self.module.build_registry([], checksum_seed=seed)

    def test_live_seed_reader_relocates_globals_but_not_runtime_pointers(self):
        base = 0x10000000
        memory = {}
        def put(address, data):
            memory.update({address + i: b for i, b in enumerate(data)})
        def word(va, value):
            put(base + va - 0x400000, struct.pack('<I', value))
        word(0x2dfaba4, 2)
        word(0x2df9d38, zlib.crc32(b'firstsecond'))
        word(0x2dfaba8, 0x20000000)
        word(0x2dfabac, 0x20000010)
        put(0x20000000, struct.pack('<II', 0x30000000, 8))
        put(0x20000010, struct.pack('<II', 0x30000100, 0))
        put(0x30000000, b'first' + bytes(123))
        put(0x30000100, b'second' + bytes(122))
        read = lambda address, length: bytes(memory[address + i] for i in range(length))
        result = self.module.read_registration(read, base)
        self.assertEqual(result['names'], ['first', 'second'])
        self.assertEqual(result['codinfo_names'], ['first'])
        self.assertEqual(result['checksum_seed'], zlib.crc32(b'firstsecond'))
        word(0x2df9d38, 1)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.module.read_registration(read, base)
        word(0x2dfaba4, 267)
        with self.assertRaisesRegex(ValueError, 'count'):
            self.module.read_registration(read, base)


if __name__ == '__main__':
    unittest.main()
