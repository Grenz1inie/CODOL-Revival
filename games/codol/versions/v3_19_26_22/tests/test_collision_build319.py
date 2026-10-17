"""Rebuildable collision helper against synthetic geometry and native gold traces."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest

from games.codol.versions.v3_19_26_22.client import native_build


FIXTURE = Path(__file__).with_name('fixtures') / 'collision319-reference.json'


def clipmap_fixture():
    header = bytearray(256)
    records = []

    def block(offset, count, data, *, count16=False):
        address = 0x10000000 + len(records) * 0x10000
        struct.pack_into('<H' if count16 else '<I', header, offset, count)
        struct.pack_into('<I', header, offset + 4, address)
        records.append((address, data))
        return address

    planes = block(8, 1, struct.pack('<4fI', -2**-.5, 0, 2**-.5, 150 * 2**-.5, 0))
    definitions = [((-200, -200, -10), (200, 200, 0), 1),
                   ((40, -200, 0), (50, 200, 100), 1),
                   ((-150, -150, 0), (-50, 150, 100), 1),
                   ((100, -25, 0), (101, 25, 70), 0x1000000),
                   ((-30, 60, 0), (30, 70, 100), 0x20)]
    sides_address = 0x20000000
    records.append((sides_address, struct.pack('<II', planes, 0)))
    brushes, bounds, contents = bytearray(), bytearray(), bytearray()
    for i, (low, high, mask) in enumerate(definitions):
        brush = bytearray(36)
        if i == 2:
            struct.pack_into('<H2xI', brush, 0, 1, sides_address)
        brushes.extend(brush)
        bounds.extend(struct.pack('<6f', *[(a+b)/2 for a,b in zip(low,high)],
                                  *[(b-a)/2 for a,b in zip(low,high)]))
        contents.extend(struct.pack('<I', mask))
    block(0x38, len(definitions), bytes(brushes), count16=True)
    for offset, data in [(0x40, bounds), (0x44, contents)]:
        address = 0x10000000 + len(records) * 0x10000
        struct.pack_into('<I', header, offset, address)
        records.append((address, data))
    vertices = [(300, -100, 0), (500, -100, 0), (300, 100, 0),
                (600, -100, 0), (800, -100, 0), (600, 100, 100)]
    block(0x64, len(vertices), b''.join(struct.pack('<3f', *v) for v in vertices))
    block(0x6c, 2, struct.pack('<6H', 0, 1, 2, 3, 5, 4))
    return b'CM319\0\0\0' + struct.pack('<I', 0x30000000) + header + b''.join(
        struct.pack('<II', address, len(data)) + data for address, data in records)


class CollisionBuildTests(unittest.TestCase):
    def test_source_build_matches_box_capsule_and_mantle_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = native_build.build(root / 'native') / 'collision319.exe'
            self.assertTrue(executable.is_file(), 'collision helper must build from repository source')
            capture = root / 'clipmap.bin'
            capture.write_bytes(clipmap_fixture())
            fixture = json.loads(FIXTURE.read_text())
            result = subprocess.run([str(executable), str(capture)],
                input='\n'.join(case['request'] for case in fixture['cases'])+'\n',
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = result.stdout.splitlines()
            self.assertEqual(lines[0], fixture['ready'])
            self.assertEqual(len(lines)-1, len(fixture['cases']))
            for case, actual in zip(fixture['cases'], lines[1:]):
                with self.subTest(case=case['name']):
                    expected = case['expected'].split()
                    if case['expected'].startswith('ERR'):
                        self.assertTrue(actual.startswith('ERR'))
                    else:
                        fields = actual.split()
                        self.assertEqual(fields[4:], expected[4:])
                        for a, b in zip(fields[:4], expected[:4]):
                            self.assertAlmostEqual(float(a), float(b), delta=0.0002)
            capture.write_bytes(capture.read_bytes()[:-5])
            invalid = subprocess.run([str(executable), str(capture)], capture_output=True, text=True, timeout=10)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertNotIn('READY', invalid.stdout)


if __name__ == '__main__':
    unittest.main()
