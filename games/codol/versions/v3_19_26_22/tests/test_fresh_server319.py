"""Server responses must work with an empty instance and tracked definitions only."""
import base64
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time
import unittest
from urllib.request import Request, urlopen
import zlib


SERVER = Path(__file__).resolve().parents[1] / 'server'


class FreshServerTests(unittest.TestCase):
    def run_server_code(self, root, code):
        result = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', code], cwd=SERVER,
            env={**os.environ, 'CODOL319_SERVER_ROOT': str(root)}, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_auth_ticket_without_memory_dump_matches_reference_response(self):
        with tempfile.TemporaryDirectory(prefix='fresh319 中文 ') as directory:
            result = self.run_server_code(directory, '''
import json
from unittest.mock import patch
from local_auth_ticket import tiger, response
with patch('time.time', return_value=1700000000):
    print(json.dumps([tiger(b'').hex(), tiger(b'abc').hex(), response({'iv_seed':12345})]))
''')
            self.assertEqual(result[:2], ['3293ac630c13f0245f92bbb1766e16167a4e58492dde73f3',
                                        '2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93'])
            reply = result[2]
            self.assertEqual((reply['auth_task'], reply['code'], reply['iv_seed']), (33, 700, 12345))
            # Fixed-time response captured before replacing the dump-backed S-boxes.
            self.assertEqual(reply['client_ticket'],
                'inG/zqZx5QqRRmHudr/g8TIdIUjgd4a72pSJlvphsLZz+QKZL+g4IlSa9DKDaIn3'
                'w5n0BCixL8aCSpdKgjfa/XR27LX6PC7VbhkJMd1lEU+JDXmyi1PDe8Ad0UR43WGP'
                'njoZkzWyz9t1IhMWXir8XKkI2QgfnnidqC4HMr8rVG4=')
            self.assertEqual(json.loads(reply['extra_data'])['username'], 'TG9jYWxQbGF5ZXI=')
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_private_profile_uses_tracked_definition_and_preserves_progress(self):
        with tempfile.TemporaryDirectory(prefix='fresh319 ') as directory:
            root = Path(directory)
            profile = root / 'profile319.json'
            original = b'{"experience":12345,"rank":4,"prestige":2,"extra":"preserve"}'
            profile.write_bytes(original)
            code = '''
import base64, json
from local_profile319 import secure_payload
print(json.dumps(base64.b64encode(secure_payload()).decode()))
'''
            for stale_definition in (None, '{"fields":[]}'):
                if stale_definition is not None:
                    (root / 'secure_fields319.json').write_text(stale_definition)
                wire = base64.b64decode(self.run_server_code(root, code))
                size = struct.unpack_from('<I', wire, 22)[0]
                blob = zlib.decompress(wire[26:26 + size])
                self.assertEqual(len(blob), 32768)
                self.assertEqual(struct.unpack_from('<II', blob, 4), (19, 2739108020))
                self.assertEqual(struct.unpack_from('<I', blob)[0], zlib.crc32(blob[4:]))
                self.assertEqual(struct.unpack_from('<i', blob, 4 + 4840)[0], 12345)
                self.assertEqual(struct.unpack_from('<ii', blob, 4 + 4879), (2, 4))
                self.assertEqual(len(wire[26 + size:]), 36 * 5)
                self.assertEqual(profile.read_bytes(), original)

    def test_http_auth_starts_without_external_certificates(self):
        with tempfile.TemporaryDirectory(prefix='http319 ') as directory:
            root = Path(directory)
            process = subprocess.Popen([sys.executable, '-B', '-X', 'utf8', str(SERVER / 'auth_capture.py'),
                '--http', '--local-response', '--port', '0', '--lifetime', '10'],
                env={**os.environ, 'CODOL319_SERVER_ROOT': directory},
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                deadline = time.monotonic() + 5
                port = None
                while time.monotonic() < deadline and process.poll() is None:
                    log = root / 'auth-capture.jsonl'
                    if log.exists():
                        events = [json.loads(line) for line in log.read_text().splitlines()]
                        port = next((event['port'] for event in events if event['event'] == 'listening'), None)
                        if port: break
                    time.sleep(0.02)
                if not port:
                    process.terminate()
                    self.fail(process.communicate(timeout=5)[1].decode(errors='replace'))
                request = Request(f'http://127.0.0.1:{port}/auth', data=b'{"iv_seed":12345}',
                                  headers={'Content-Type':'application/json'})
                with urlopen(request, timeout=5) as response:
                    self.assertEqual(json.load(response)['code'], 700)
                self.assertFalse(list(root.glob('*.pem')))
            finally:
                if process.poll() is None: process.terminate()
                process.communicate(timeout=5)


if __name__ == '__main__':
    unittest.main()
