"""The migrated host is exercised through a real loopback UDP socket."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest


class MatchHostTests(unittest.TestCase):
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
