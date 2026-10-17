"""Wire compatibility with fixed 3.19 native reference outputs."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOST = Path(__file__).resolve().parents[1] / 'server/match_host'
FIXTURE = Path(__file__).with_name('fixtures') / 'snapshot319-reference.json'


class SnapshotCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('snapshot_codec319', HOST / 'snapshot_codec319.py')
        cls.codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.codec)

    def test_wire_matches_native_reference_without_package_or_subprocess(self):
        fixture = json.loads(FIXTURE.read_text())
        weapon, body, hands, flags = fixture['arguments']
        for case in fixture['cases']:
            with self.subTest(case=case['name']):
                if case['expected'].startswith('ERR'):
                    with self.assertRaises(ValueError):
                        self.codec.encode(case['request'], weapon, (body, hands), flags)
                else:
                    payload = self.codec.encode(case['request'], weapon, (body, hands), flags)
                    self.assertEqual(payload.hex(), case['expected'].split()[0])

    def test_calls_do_not_keep_previous_frame_overrides(self):
        request = '1000 1000 1370 -384 248 0 0 0 0 180 0 2046'
        initial = self.codec.encode(request, 187, (4, 5), 128)
        self.codec.encode(request + ' F900=1 F901=0', 187, (4, 5), 128)
        self.assertEqual(self.codec.encode(request, 187, (4, 5), 128), initial)

    def test_live_sim_works_without_native_executable_and_switches_weapon(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-B', '-I', '-c', '''
import sys
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from live_sim319 import LiveSim
from snapshot_stream319 import validate_initial_payload
with patch('subprocess.Popen', side_effect=AssertionError('Native snapshot dependency')):
    sim = LiveSim([1370, -384, 248], yaw=180, weapon=187, viewmodels=(4, 5), weapflags=128)
    initial = sim.payload(1000)
    assert validate_initial_payload(initial) == 1000
    sim.set_weapon(78)
    assert sim.payload(1000) != initial
    sim.close()
''', str(HOST)], env={**os.environ, 'CODOL319_SERVER_ROOT': directory},
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_initial_snapshot_matches_historical_floor_baseline(self):
        from games.codol.versions.v3_19_26_22.client import match
        reference = json.loads(FIXTURE.read_text())['initial_payload_hex']
        self.assertEqual(match.initial_snapshot().hex(), reference)


if __name__ == '__main__':
    unittest.main()
