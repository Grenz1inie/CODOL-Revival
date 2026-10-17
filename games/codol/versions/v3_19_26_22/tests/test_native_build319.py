"""Build and load the replacement DLLs without any imported startup package."""
import os
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pefile

from games.codol.versions.v3_19_26_22.client import native_build


@unittest.skipUnless(os.name == 'nt', 'Windows x86 DLL consumer')
class NativeBuildTests(unittest.TestCase):
    def test_build_load_identity_guards_and_predicted_state_consumer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            built = native_build.build(root / 'native')
            with pefile.PE(str(built / 'ifs-read.exe')) as reader:
                self.assertEqual(reader.FILE_HEADER.Machine, 0x14c)
            usage = subprocess.run([str(built / 'ifs-read.exe')], capture_output=True, timeout=5)
            self.assertEqual(usage.returncode, 2)
            self.assertIn(b'ARCHIVE_COPY', usage.stderr)
            for name in ('version.dll', 'client_loopback319.dll'):
                with pefile.PE(str(built / name)) as image:
                    self.assertEqual(image.FILE_HEADER.Machine, 0x14c)
            with pefile.PE(str(built / 'version.dll')) as proxy:
                self.assertEqual(len(proxy.DIRECTORY_ENTRY_EXPORT.symbols), 17)
                self.assertTrue(all(s.forwarder.startswith(b'version_system319.') for s in proxy.DIRECTORY_ENTRY_EXPORT.symbols))
            shutil.copyfile(Path(os.environ['SystemRoot']) / 'SysWOW64/version.dll', root / 'version_system319.dll')
            (root / 'codol319-root.txt').write_text(str(built) + '\\\n')
            (built / 'arm-loopback319.txt').write_text('0')
            compiler = native_build.compiler()
            executable = root / 'codoMP_client_shipRetail.exe'
            result = subprocess.run([compiler, '-m32', '-std=c99', '-O2', '-static-libgcc',
                '-Wl,--image-base,0x400000', '-o', str(executable),
                str(Path(__file__).parent / 'fixtures/bridge-consumer.c'), str(native_build.SOURCE / 'capture.c')],
                env=native_build.compiler_env(compiler), capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            loaded = subprocess.run([str(executable), str(built)], cwd=root,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(loaded.returncode, 0, loaded.stdout + loaded.stderr)
            state = (built / 'predicted-ps319.bin').read_bytes()
            self.assertEqual(state[:4], b'PS19')
            self.assertEqual(state[4:8], state[-4:])
            self.assertEqual(state[12:16], bytes.fromhex('78563412'))
            capture = next(root.glob('config319-*-first-netchan.txt'))
            decoded = subprocess.run([sys.executable, '-B', '-c', '''
import hashlib,json,sys
from inspect_config_capture319 import parse_capture
from reconstruct_ncs319 import reconstruct
from pathlib import Path
result,_=reconstruct(parse_capture(Path(sys.argv[1])))
print(json.dumps(dict(checksum=result['predicted_checksum_hex'].lower(),nodes=str(result['nodes']),
 strings=str(result['strings']),types_sha256=hashlib.sha256(bytes.fromhex(result['type_table_hex'])).hexdigest())))
''', str(capture)], cwd=Path(__file__).resolve().parents[1] / 'server/match_host',
                capture_output=True, text=True, timeout=10)
            self.assertEqual(decoded.returncode, 0, decoded.stderr)
            reference = json.loads((Path(__file__).parent / 'fixtures/ncs319-reference.json').read_text())
            self.assertEqual(json.loads(decoded.stdout), reference['expected'])
            self.assertFalse(list(root.glob('config319-*.tmp')))
            # A usable build can be reused on machines without the compiler.
            before = {p.name: p.read_bytes() for p in built.glob('*.dll')}
            with patch.dict(os.environ, {'CODOL319_CC': str(root / 'missing-gcc.exe')}):
                self.assertEqual(native_build.build(built), built)
                (built / 'client_loopback319.dll').write_bytes(b'damaged')
                with self.assertRaisesRegex(RuntimeError, 'MinGW'):
                    native_build.build(built)
            self.assertEqual((built / 'version.dll').read_bytes(), before['version.dll'])


if __name__ == '__main__':
    unittest.main()
