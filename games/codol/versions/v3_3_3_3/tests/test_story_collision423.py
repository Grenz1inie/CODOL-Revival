"""Actual first-map geometry at the native collision conversion boundary."""
import importlib.util
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]


class Collision423Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory(dir=ROOT / 'research/experiments/story-native')
        cls.addClassCleanup(cls.folder.cleanup)
        cls.executable = Path(cls.folder.name) / 'collision-probe.exe'
        cls.env = dict(os.environ, PATH='A:/Coding/MinGW/bin;C:/Windows/System32;C:/Windows')
        subprocess.run(['A:/Coding/MinGW/bin/gcc.exe', '-Os', '-static-libgcc',
                        str(ROOT / 'games/codol/versions/v3_3_3_3/tests/native/story_collision_probe.c'),
                        str(ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/native/story_collision423.c'), '-o', str(cls.executable)],
                       env=cls.env, check=True, capture_output=True)
        spec = importlib.util.spec_from_file_location('index_story_zone', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/index_story_zone.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        zone = (ROOT / 'research/experiments/story-native/zone-assets/mp_cargoship/zone.bin').read_bytes()
        cls.asset = next(data for kind, data in module.read_assets(zone) if kind == 15)

    def probe(self, data, kind=15, version=423):
        path = Path(self.folder.name) / 'collision.bin'
        path.write_bytes(data)
        result = subprocess.run([str(self.executable), str(path), str(kind), str(version)],
                                env=self.env, capture_output=True, text=True, timeout=10)
        return result.returncode, [int(s) for s in result.stdout.splitlines()]

    def test_current_map_preserves_geometry_counts_and_source_ranges(self):
        code, layout = self.probe(self.asset)
        self.assertEqual(code, 0, 'Current collision asset must yield a usable layout')
        self.assertEqual(len(layout), 86)
        # Independent counts from the current client header and array consumers.
        for row, count, stride in ((0, 18346, 20), (1, 9173, 76), (2, 929, 12),
                                   (6, 5071, 40), (8, 26082, 20), (10, 49762, 12),
                                   (11, 68916, 6), (16, 290, 72), (17, 27472, 36)):
            with self.subTest(row=row):
                offset, actual, width, pointer = layout[row * 4:row * 4 + 4]
                self.assertEqual((actual, width), (count, stride))
                if offset != 0xffffffff:
                    self.assertLessEqual(offset + actual * width, len(self.asset))
        self.assertGreater(layout[84], 256)
        # All live leaf references are inline; the unused shared storage alias
        # must not be counted a second time by the reference brush-tree builder.
        self.assertEqual(layout[29], 0)

    def test_invalid_version_type_header_and_truncated_arrays_are_rejected(self):
        for data, kind, version in ((self.asset, 15, 365), (self.asset, 42, 423),
                                     (b'', 15, 423), (self.asset[:255], 15, 423),
                                     (self.asset[:4096], 15, 423)):
            with self.subTest(length=len(data), kind=kind, version=version):
                self.assertEqual(self.probe(data, kind, version)[0], 1)
        bad = bytearray(self.asset)
        struct.pack_into('<I', bad, 0x64, 0xffffffff)
        self.assertEqual(self.probe(bad)[0], 1)


if __name__ == '__main__':
    unittest.main()
