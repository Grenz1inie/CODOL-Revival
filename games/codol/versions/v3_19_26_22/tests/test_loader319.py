"""Shared-memory consumer and guarded writes for the source-built bootstrap."""
import ctypes
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import loader, preparation


class LoaderTests(unittest.TestCase):
    def test_metadata_matches_native_launcher_contract(self):
        data = loader.metadata()
        self.assertEqual(len(data), 0x100000)
        integer = lambda offset: struct.unpack_from('<I', data, offset)[0]

        def value(table, key):
            offset = integer(table + key * 4)
            length = integer(offset)
            self.assertLessEqual(offset + 4 + length, len(data))
            return data[offset + 4:offset + 4 + length]

        self.assertEqual(integer(0), 64)
        self.assertEqual(value(0, 2), struct.pack('<I', 1000001))
        self.assertEqual(value(0, 7), b'127.0.0.1:31900\0')
        self.assertEqual(value(0, 24), b'LocalPlayer\0')
        self.assertEqual(value(0, 22), bytes(16))
        group_index = integer(0x50)
        group = integer(group_index)
        self.assertEqual(value(group, 1), 'Local CODOL 3.19\0'.encode('utf-16le'))
        self.assertEqual(value(group, 3), '127.0.0.1\0'.encode('utf-16le'))
        self.assertEqual(value(group, 4), bytes([127, 0, 0, 1]))
        self.assertEqual(value(group, 5), struct.pack('<I', 31900))
        self.assertEqual(value(group, 7), b'127.0.0.1:31900;127.0.0.1:31901;1\0')
        for key in range(256):
            self.assertEqual(value(integer(group_index + 255 * 4), key), bytes(4))

    @unittest.skipUnless(os.name == 'nt', 'Windows process memory API')
    def test_patch_requires_exact_original_bytes_and_preserves_adjacent_bytes(self):
        original, replacement = b'\xb8\x02\x0c\0\0', b'\xb8\x04\x0c\0\0'
        memory = ctypes.create_string_buffer(b'<' + original + b'>')
        address = ctypes.addressof(memory) + 1
        with loader.ProcessMemory(os.getpid()) as process:
            self.assertFalse(process.patch(address, b'wrong', replacement))
            self.assertEqual(memory.raw, b'<' + original + b'>\0')
            self.assertTrue(process.patch(address, original, replacement))
            self.assertEqual(memory.raw, b'<' + replacement + b'>\0')
            self.assertTrue(process.patch(address, original, replacement))
            self.assertFalse(process.patch(1, original, replacement))

    @unittest.skipUnless(os.name == 'nt', 'Windows bootstrap')
    def test_owned_child_consumes_metadata_and_patches_without_external_loader(self):
        compiler = shutil.which(os.environ.get('CODOL319_CC', 'gcc'))
        if not compiler:
            self.skipTest('Requires the declared MinGW toolchain')
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            executable = game / preparation.CLIENT
            fixture = Path(__file__).parent / 'fixtures/bootstrap-consumer.c'
            built = subprocess.run([compiler, '-m32', '-std=c99', '-O2', '-static-libgcc',
                '-Wl,--image-base,0x400000', '-o', str(executable), str(fixture)],
                env={**os.environ, 'PATH': str(Path(compiler).parent) + os.pathsep + os.environ['PATH']},
                capture_output=True, text=True, timeout=30)
            self.assertEqual(built.returncode, 0, built.stderr)
            original = executable.read_bytes()
            with patch.object(preparation, 'CLIENT_SHA256', hashlib.sha256(original).hexdigest()), \
                    patch.dict(os.environ, {'CODOL319_EXTRA_ARGS': ''}):
                self.assertEqual(loader.run(game), 0)
            self.assertEqual(executable.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
