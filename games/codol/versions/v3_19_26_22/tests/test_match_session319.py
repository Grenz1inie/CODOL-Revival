"""Local-asset integration: Ready gates the real native-backed match host."""
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest

import psutil

from games.codol.versions.v3_19_26_22.client import match
from games.codol.versions.v3_19_26_22.client.lifecycle import identity, service_status


class MatchSessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        package = Path(__file__).resolve().parents[5] / 'runtime/packages/codol-3.19.26.22'
        if not package.exists():
            raise unittest.SkipTest('Requires the imported user-supplied 3.19 test-build assets')
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.runtime = Path(cls.temp.name)
        (cls.runtime / 'game').mkdir()
        for name in match.ASSETS:
            target = cls.runtime / 'server' / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(package / 'server' / name, target)

    def setUp(self):
        self.log = self.runtime / 'server/lsg-handshake.jsonl'
        self.log.write_text('')
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(('127.0.0.1', 0))
            self.port = sock.getsockname()[1]
        self.since = time.time()
        self.session = match.MatchSession(self.runtime, identity(os.getpid()), self.since, port=self.port)
        self.addCleanup(self.session.close)

    def ready(self):
        self.log.write_text(json.dumps({'event':'room_ready', 'time':self.since + 1}) + '\n{"partial"')
        return self.session.poll()

    def test_only_fresh_ready_starts_once_and_close_reaps_native_children(self):
        self.log.write_text('{"event":"room_ready","time":1}\n')
        self.assertEqual(self.session.poll()['phase'], 'waiting')
        state = self.ready()
        self.assertEqual(state['phase'], 'running', state)
        self.assertTrue(service_status([state['service']])['ready'])
        marker = self.runtime / 'server/match-host/arm-loopback319.txt'
        self.assertEqual(marker.read_text(), str(os.getpid()))
        children = psutil.Process(state['service']['pid']).children(recursive=True)
        self.assertTrue(children, 'The migrated host must use the real collision helper')
        self.assertEqual(self.session.poll()['service'], state['service'])
        self.session.close()
        self.assertEqual(marker.read_text(), '0')
        self.assertFalse(service_status([state['service']])['running'])
        # Windows conhost descendants may finish just after the native child exits.
        _, remaining = psutil.wait_procs(children, timeout=2)
        self.assertEqual(remaining, [])
        self.assertEqual(self.session.poll()['phase'], 'finished')

    def test_foreign_udp_conflict_does_not_arm_or_stop_the_foreign_socket(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as foreign:
            foreign.bind(('127.0.0.1', self.port))
            state = self.ready()
            self.assertEqual(state['phase'], 'error')
            self.assertIn(str(self.port), state['error'])
            self.assertEqual((self.runtime / 'server/match-host/arm-loopback319.txt').read_text(), '0')
            self.assertIsNone(state['service'])
            self.assertEqual(foreign.getsockname()[1], self.port)
        self.assertEqual(self.session.poll()['phase'], 'error')

    def test_changed_native_dependency_fails_before_arm_or_host_start(self):
        path = self.runtime / 'server/match-host/mainframe-verification/snapshot319_live.exe'
        original = path.read_bytes()
        try:
            path.write_bytes(b'unknown binary')
            state = self.ready()
            self.assertEqual(state['phase'], 'error')
            self.assertIn('snapshot319_live.exe', state['error'])
            self.assertIsNone(state['service'])
            self.assertEqual((self.runtime / 'server/match-host/arm-loopback319.txt').read_text(), '0')
        finally:
            path.write_bytes(original)

    def test_stale_game_identity_never_starts_match(self):
        self.session.game = {'pid': os.getpid(), 'created': 0}
        self.assertNotEqual(self.ready()['phase'], 'running')
        self.assertIsNone(self.session.poll()['service'])

    def test_native_snapshot_and_loadout_tables_use_instance_assets(self):
        source = Path(__file__).resolve().parents[1] / 'server/match_host'
        code = '''
import json, os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from collision_move319 import Collision
from live_sim319 import LiveSim
from playerdata_classes319 import classes, weapon_index
from weapon_composite319 import compose
root = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
collision = Collision(root / 'collision319/config319-27572-clipmap.bin')
sim = LiveSim([1370,-384,248], yaw=180, weapon=187, viewmodels=(4,5), weapflags=128, collision=collision)
try:
    payload = sim.payload(1000)
    print(json.dumps({'snapshot':payload.hex(), 'classes':len(classes(bytes(32764))),
                      'weapon':weapon_index(10001), 'parts':compose(10001, [])}))
finally:
    sim.close()
    collision.close()
'''
        result = subprocess.run([sys.executable, '-B', '-I', '-c', code, str(source)],
            env={**os.environ, 'CODOL319_SERVER_ROOT':str(self.runtime / 'server')},
            capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        snapshot = bytes.fromhex(data['snapshot'])
        self.assertEqual(snapshot[:7], b'\x00\xe8\x03\x00\x00\x00\x08')
        self.assertEqual(snapshot[-1], 5)
        self.assertEqual(data['classes'], 60)
        self.assertEqual(data['weapon'][1], 'm4_mp')
        self.assertTrue(data['parts'][0])
