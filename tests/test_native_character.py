"""Current public character reader, using captured offsets and an isolated C DLL."""
import ctypes
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'research/experiments/story-native'


class NativeCharacterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / 'research/evidence/live-player-schema.json').read_text())['schemas']['mp/playerdata.def']
        cls.scratch = tempfile.TemporaryDirectory(dir=STAGE)
        cls.addClassCleanup(cls.scratch.cleanup)
        source = STAGE / 'server3333/src/codol'
        compiler = Path('A:/Coding/mingw64/bin')
        files = [ROOT / 'tests/native/story_character.c'] + [source / 'stats' / name for name in (
            'codol_profile_character.c', 'codol_profile.c',
            'codol_structured_schema.c', 'codol_structured_data.c')]
        dll = Path(cls.scratch.name) / 'character.dll'
        subprocess.run([str(compiler / 'gcc.exe'), '-shared', '-O1', '-std=gnu11',
            '-ffunction-sections', '-fdata-sections', '-fno-asynchronous-unwind-tables',
            '-Wl,--gc-sections,--exclude-all-symbols',
            '-I' + str(source / 'stats'), '-I' + str(source / 'assets'),
            *map(str, files), '-o', str(dll)], check=True, capture_output=True,
            env=dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32'))
        cls.lib = ctypes.CDLL(str(dll))
        import _ctypes
        cls.addClassCleanup(_ctypes.FreeLibrary, cls.lib._handle)
        cls.read = cls.lib.story_character_read
        cls.read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                             ctypes.c_uint32, ctypes.c_uint, ctypes.c_char_p, ctypes.c_void_p]
        cls.read.restype = ctypes.c_int

    def setUp(self):
        self.offsets = list(self.schema['offsets'])
        self.profile = bytearray(32768)
        self.checksum = self.schema['header'][1]
        self.record_size = self.schema['header'][12]
        self.schema_name = b'mp/playerdata.def'
        struct.pack_into('<II', self.profile, 4, 233, self.checksum)
        self.profile[4 + self.offsets[697]] = 11
        for i, value in enumerate([545, 104, 0, 0xffffffff, 0, 0, 0, 0, 0]):
            self.write_slot(i, value)

    def write_slot(self, index, value):
        struct.pack_into('<I', self.profile, 4 + self.offsets[576 + 11 * 10 + 1 + index], value)

    def result(self):
        profile = ctypes.create_string_buffer(bytes(self.profile))
        offsets = ctypes.create_string_buffer(struct.pack('<' + 'I' * len(self.offsets), *self.offsets))
        out = (ctypes.c_uint16 * 10)(*[0xaaaa] * 10)
        status = self.read(profile, offsets, len(self.offsets) * 4, self.checksum,
                           self.record_size, self.schema_name, out)
        if not status:
            self.assertEqual(list(out), [0xaaaa] * 10)
        return status, list(out)

    def test_current_schema_selects_last_character_and_normalizes_unselected_slot(self):
        before = bytes(self.profile)
        self.assertEqual(self.result(), (1, [11, 545, 104, 0, 0, 0, 0, 0, 0, 0]))
        self.assertEqual(bytes(self.profile), before)

    def test_zero_header_uses_bound_current_public_schema_without_mutating_data(self):
        self.profile[4:12] = bytes(8)
        before = bytes(self.profile)
        self.assertEqual(self.result(), (1, [11, 545, 104, 0, 0, 0, 0, 0, 0, 0]))
        self.assertEqual(bytes(self.profile), before)

    def test_zero_header_does_not_select_old_or_unknown_schema(self):
        self.profile[4:12] = bytes(8)
        self.checksum = 0x70cd4cc5
        self.assertEqual(self.result()[0], 0)
        self.checksum = self.schema['header'][1]
        self.record_size -= 1
        self.assertEqual(self.result()[0], 0)

    def test_zero_header_does_not_apply_to_private_profile(self):
        self.profile[4:12] = bytes(8)
        self.schema_name = b'mp/playersecuredata.def'
        self.assertEqual(self.result()[0], 0)

    def test_mismatched_schema_header_is_rejected(self):
        struct.pack_into('<I', self.profile, 8, 0x70cd4cc5)
        self.assertEqual(self.result()[0], 0)

    def test_character_index_outside_twelve_records_is_rejected(self):
        self.profile[4 + self.offsets[697]] = 12
        self.assertEqual(self.result()[0], 0)

    def test_empty_package_and_non_item_values_are_rejected(self):
        for value in (0, 0xffffffff, 65536):
            with self.subTest(value=value):
                self.write_slot(0, value)
                self.assertEqual(self.result()[0], 0)

    def test_slot_outside_record_is_rejected(self):
        self.offsets[576 + 11 * 10 + 9] = self.record_size
        self.assertEqual(self.result()[0], 0)


if __name__ == '__main__':
    unittest.main()
