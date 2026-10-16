import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ProfileRuntimeTests(unittest.TestCase):
    def test_two_instances_read_and_write_only_their_own_profiles(self):
        server = Path(__file__).resolve().parents[1] / 'server'
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / name for name in ('First', 'Second')]
            for root in roots:
                root.mkdir()
                (root / 'profile319.json').write_text(json.dumps({'name': root.name}))
                script = ("from local_profile319 import player_name,save_public_info,load_public_info; "
                          "save_public_info(1000001,player_name().encode()); print(load_public_info(1000001).decode())")
                result = subprocess.run([sys.executable, '-B', '-c', script], cwd=server,
                    env={**os.environ, 'CODOL319_SERVER_ROOT': str(root)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), root.name)
            self.assertEqual((roots[0] / 'local-profiles319/1000001-public.bin').read_bytes(), b'First')
            self.assertEqual((roots[1] / 'local-profiles319/1000001-public.bin').read_bytes(), b'Second')
