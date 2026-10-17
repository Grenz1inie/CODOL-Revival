import json
import os
from pathlib import Path
import socket
import tempfile
import time
import unittest
from unittest.mock import patch
from games.codol.versions.v3_19_26_22.client import match
from games.codol.versions.v3_19_26_22.client.lifecycle import identity, service_status


class NuketownMatchTests(unittest.TestCase):
    @patch('games.codol.versions.v3_19_26_22.client.nuketown_assets.build')
    def test_ready_routes_to_rust_and_waits_for_this_process_capture(self, build):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'server/match-host').mkdir(parents=True)
            (root / 'game').mkdir()
            spawn = root / 'spawn.json'
            spawn.write_text(json.dumps({'map':'mp_nuked', 'origin':[100,200,300], 'yaw':90}))
            build.return_value = spawn
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            since = time.time()
            session = match.MatchSession(root, identity(os.getpid()), since, port=port)
            fixture = Path(__file__).resolve().parent
            roster = (fixture.parent / 'server/native/match-server/tests/fixtures/roster-native.bin').read_bytes()
            request = {'time': since - 1, 'uid': 1000001, 'name': 'Player', 'roster': list(roster)}
            path = root / 'server/nuketown-ready.json'
            path.write_text(json.dumps(request))
            try:
                self.assertEqual(session.poll()['phase'], 'waiting')
                request['time'] = time.time()
                path.write_text(json.dumps(request))
                state = session.poll()
                self.assertEqual(state['phase'], 'running', state)
                self.assertTrue(service_status([state['service']])['ready'])
                self.assertEqual(state['map'], 'mp_nuked')
                run = Path(state['run'])
                self.assertEqual(json.loads((run/'room.json').read_text())['spawn_file'], str(spawn))
                build.assert_called_once()
                self.assertFalse((run / 'gamestate.bin').exists())
                capture = root / 'game' / f'config319-{os.getpid()}-first-netchan.txt'
                source = (fixture / 'fixtures/ncs319-capture.txt').read_text()
                capture.write_text(source.split('database_nodes=')[0])
                session.poll()
                self.assertFalse((run / 'gamestate.bin').exists())
                capture.write_text(source)
                session.poll()
                state_bytes = (run / 'gamestate.bin').read_bytes()
                self.assertEqual(state_bytes[:5], bytes([3, 0, 0, 0, 0]))
                self.assertIn(b'mp_nuked\0cha\0', state_bytes)
                self.assertNotIn(b'mp_seatown', state_bytes)
                self.assertEqual(session.poll()['service'], state['service'])
            finally:
                session.close()
            self.assertEqual((root / 'server/match-host/arm-loopback319.txt').read_text(), '0')
            self.assertFalse(service_status([state['service']])['running'])
