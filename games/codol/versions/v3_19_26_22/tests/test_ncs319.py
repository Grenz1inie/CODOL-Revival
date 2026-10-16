"""NCS reconstruction against a fixed native reference, without an external package."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOST = Path(__file__).resolve().parents[1] / 'server/match_host'
FIXTURE = Path(__file__).resolve().parent / 'fixtures/ncs319-reference.json'


class NcsTests(unittest.TestCase):
    def test_fresh_instance_reconstructs_native_checksum_and_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-B', '-c', '''
import hashlib, json, sys
from reconstruct_ncs319 import reconstruct
fixture=json.load(open(sys.argv[1]))
prediction,wire=reconstruct(fixture['capture'])
print(json.dumps(dict(checksum=prediction['predicted_checksum_hex'].lower(),
    nodes=str(prediction['nodes']),strings=str(prediction['strings']),
    types_sha256=hashlib.sha256(bytes.fromhex(prediction['type_table_hex'])).hexdigest())))
''', str(FIXTURE)], cwd=HOST, env={**os.environ, 'CODOL319_SERVER_ROOT': directory},
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), json.loads(FIXTURE.read_text())['expected'])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_map_message_needs_no_native_verifier_or_dump(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            capture=root/'capture.txt'
            original=FIXTURE.with_name('ncs319-capture.txt').read_text()
            capture.write_text(original)
            result=subprocess.run([sys.executable, '-B', '-c', '''
import hashlib, json, sys
from pathlib import Path
from gamestate_probe319 import build_probe
capture=Path(sys.argv[1])
payload,_=build_probe(capture,map_name='mp_seatown',game_type='tdm',output_dir=capture.parent)
capture.write_text(capture.read_text().split('database_nodes=')[0])
incomplete=build_probe(capture,map_name='mp_seatown',game_type='tdm',output_dir=capture.parent)
print(json.dumps([hashlib.sha256(payload).hexdigest(),incomplete]))
''',str(capture)],cwd=HOST,env={**os.environ,'CODOL319_SERVER_ROOT':directory},
                capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout),[json.loads(FIXTURE.read_text())['gamestate_sha256'],None])


if __name__ == '__main__':
    unittest.main()
