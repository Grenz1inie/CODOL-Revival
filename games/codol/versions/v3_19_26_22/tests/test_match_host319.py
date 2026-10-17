"""The migrated host is exercised through a real loopback UDP socket."""
import json
from contextlib import ExitStack
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch


class MatchHostTests(unittest.TestCase):
    def test_collision_reads_ladders_beside_the_current_map(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, CODOL319_SERVER_ROOT=directory):
            from games.codol.versions.v3_19_26_22.server.match_host import collision_move319 as module
            root = Path(directory)
            target = root/'clipmap.bin'
            ladders = [{'mins': [0,0,0], 'maxs': [10,10,100]}]
            target.with_suffix('.ladders.json').write_text(json.dumps(ladders))
            process = Mock()
            process.stdout.readline.return_value = 'READY\n'
            with patch.object(module, 'ROOT', root), patch.object(module.subprocess, 'Popen', return_value=process) as spawn:
                collision = module.Collision(target)
                self.assertEqual(collision.ladders, ladders)
                self.assertEqual(spawn.call_args.args[0], [str(root/'collision319.exe'), str(target)])
                movement = module.CollisionMovement()
                movement.origin, movement.collision = [5,5,50], collision
                self.assertEqual(movement.ladder_at(), ladders[0])
                target.with_suffix('.ladders.json').unlink()
                with self.assertRaises(FileNotFoundError):
                    module.Collision(target)
                self.assertEqual(spawn.call_count, 1)

    def test_current_map_is_exported_after_load_before_first_snapshot(self):
        from games.codol.versions.v3_19_26_22.client.match import initial_snapshot
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, CODOL319_SERVER_ROOT=directory), ExitStack() as cleanup:
            from games.codol.versions.v3_19_26_22.server.match_host import diag_host319 as module
            root = Path(directory)
            snapshot = root / 'snapshot.bin'
            snapshot.write_bytes(initial_snapshot())
            target = root / 'clipmap.bin'
            game = (123, 4.5, str(root / 'game.exe'))
            with patch.object(module, 'load_server_commands', return_value=[]), \
                    patch.object(module, 'export_map') as export, \
                    patch('collision_move319.Collision') as collision, \
                    patch('live_sim319.LiveSim'):
                host = module.DiagHost(0, 'mp_seatown', 'tdm', 18, 1, root / 'run',
                    gamestate_capture=root/'netchan.txt', snapshot_payload=snapshot,
                    delta_continuation=True, ack_client_commands=True, live_seconds=1,
                    collision_map=target, resource_game=game)
                cleanup.callback(host.jsonl.close)
                export.assert_not_called()
                collision.assert_not_called()
                sock, peer = Mock(), ('127.0.0.1', 123)
                packet = b'\xff\xff\xff\xffgamestateupdate 6\0'
                host.handle(sock, packet, peer)
                export.assert_not_called()
                host.connected.add(peer)
                host.stats_uploads[peer] = SimpleNamespace(profile=bytes(32768))
                host.gamestate_sequences[peer] = 3
                host.connect_challenge[peer] = 7
                export.side_effect = ValueError('wrong map')
                with self.assertRaisesRegex(ValueError, 'wrong map'):
                    host.handle(sock, packet, peer)
                sock.sendto.assert_not_called()
                self.assertNotIn(peer, host.snapshot_attempted)
                order = []
                export.side_effect = lambda *a: order.append('export')
                collision.side_effect = lambda *a: order.append('collision') or Mock()
                sock.sendto.side_effect = lambda *a: order.append('snapshot')
                host.handle(sock, packet, peer)
                export.assert_called_with(target, {'pid': 123, 'created': 4.5}, root/'game.exe', 'mp_seatown')
                self.assertEqual(order, ['export', 'collision', 'snapshot'])
                host.handle(sock, packet, peer)
                self.assertEqual(order, ['export', 'collision', 'snapshot'])

    def test_owned_host_serves_current_version_handshake_and_ignores_malformed_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reserved:
                reserved.bind(('127.0.0.1', 0))
                port = reserved.getsockname()[1]
            script = Path(__file__).resolve().parents[1] / 'server/match_host/diag_host319.py'
            host = subprocess.Popen([sys.executable, '-B', '-I', str(script), '--port', str(port),
                '--seconds', '300', '--logdir', str(root / 'run'), '--stop-file', str(root / 'stop.request')], cwd=root,
                env={**os.environ, 'CODOL319_SERVER_ROOT': str(root / 'server')},
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                log = root / 'run/diag-host319.jsonl'
                deadline = time.monotonic() + 5
                while not log.exists() and host.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertIsNone(host.poll(), host.stdout.read() if host.poll() is not None else '')
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
                    client.settimeout(2)
                    peer = ('127.0.0.1', port)
                    client.sendto(b'\xff\xff\xff\xffgetchallenge invalid\x00', peer)
                    client.sendto(b'\xff\xff\xff\xffgetchallenge 0 "test319"\x00', peer)
                    challenge = client.recv(2048).split(b'challengeResponse ')[1].rstrip(b'\x00\n')
                    self.assertTrue(challenge.isdigit())
                    client.sendto(b'\xff\xff\xff\xffconnect 00000000000f4241 "\\challenge\\' + challenge + b'\\qport\\123\\protocol\\1"\x00', peer)
                    response = client.recv(2048)
                    self.assertIn(b'connectResponse \\mapname\\mp_seatown\\gametype\\tdm', response)
                (root / 'stop.request').touch()
                stdout, _ = host.communicate(timeout=7)
                self.assertEqual(host.returncode, 0, stdout)
                events = [json.loads(line)['event'] for line in log.read_text().splitlines()]
                self.assertIn('oob_unhandled', events)
                self.assertIn('stopped', events)
                self.assertFalse((root / 'server/profile319.json').exists())
            finally:
                if host.poll() is None:
                    host.kill()
                    host.wait(timeout=5)
                host.stdout.close()
