"""First-install setup through its public entry point, using disposable game files."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import ssl
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_3_3_3.client import bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='CODOL setup 中文 ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game, self.runtime = self.root / 'game', self.root / 'instance'
        self.game.mkdir()
        (self.game / 'codoMP_client_shipRetail.exe').write_bytes(b'client fixture')
        self.original = {'dwauth.ini': b'old-auth 3074\r\nold-auth 443\r\n0x03EA\r\n',
                         'stun.ini': b'old-stun\r\n', 'cacert.pem': b'# original trust bundle\r\n'}
        for name, data in self.original.items(): (self.game / name).write_bytes(data)
        identity = patch.object(bootstrap, 'CLIENT_SHA256', hashlib.sha256(b'client fixture').hexdigest())
        identity.start()
        self.addCleanup(identity.stop)

    def test_new_instance_prepares_client_trust_and_retains_original_files(self):
        self.runtime.mkdir()
        (self.runtime / 'instance.json').write_text('{}')
        bootstrap.prepare(self.game, self.runtime)
        self.assertEqual((self.game / 'dwauth.ini').read_text().split(),
                         ['127.0.0.1', '3074', '127.0.0.1', '443', '0x03EA'])
        self.assertEqual((self.game / 'stun.ini').read_text().strip(), '127.0.0.1')
        trust = (self.game / 'cacert.pem').read_bytes()
        self.assertTrue(trust.startswith(self.original['cacert.pem']))
        self.assertIn((self.runtime / 'certs/ca.pem').read_bytes().strip(), trust)
        for name, original in self.original.items():
            self.assertEqual((self.runtime / 'backups/client-config' / name).read_bytes(), original)
        server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server.load_cert_chain(self.runtime / 'certs/server.pem', self.runtime / 'certs/server-key.pem')
        client = ssl.create_default_context(cafile=str(self.game / 'cacert.pem'))
        incoming, outgoing = ssl.MemoryBIO(), ssl.MemoryBIO()
        peer_in, peer_out = ssl.MemoryBIO(), ssl.MemoryBIO()
        left = client.wrap_bio(incoming, outgoing, server_hostname='127.0.0.1')
        right = server.wrap_bio(peer_in, peer_out, server_side=True)
        for _ in range(8):
            for connection in (left, right):
                try: connection.do_handshake()
                except ssl.SSLWantReadError: pass
            if outgoing.pending: peer_in.write(outgoing.read())
            if peer_out.pending: incoming.write(peer_out.read())
        left.write(b'client trusted this instance')
        peer_in.write(outgoing.read())
        self.assertEqual(right.read(), b'client trusted this instance')

    def test_repeat_keeps_identity_backup_and_progress_and_deduplicates_trust(self):
        bootstrap.prepare(self.game, self.runtime)
        (self.runtime / 'player.bin').write_bytes(b'progress')
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        bootstrap.prepare(self.game, self.runtime)
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob('*') if p.is_file()})

    def test_incomplete_invalid_or_expired_identity_is_backed_up_and_repaired(self):
        for damage in ('missing', 'key', 'expired', 'future'):
            with self.subTest(damage=damage):
                runtime = self.root / damage
                if damage in ('expired', 'future'):
                    days = -400 if damage == 'expired' else 400
                    with patch.object(bootstrap, 'datetime', wraps=datetime) as clock:
                        clock.now.return_value = datetime.now(timezone.utc) + timedelta(days=days)
                        bootstrap.prepare(self.game, runtime)
                else:
                    bootstrap.prepare(self.game, runtime)
                old_ca = (runtime / 'certs/ca.pem').read_bytes()
                if damage == 'missing': (runtime / 'certs/server.pem').unlink()
                if damage == 'key': (runtime / 'certs/server-key.pem').write_bytes(b'broken')
                bootstrap.prepare(self.game, runtime)
                self.assertNotEqual(old_ca, (runtime / 'certs/ca.pem').read_bytes())
                self.assertTrue(any(p.read_bytes() == old_ca for p in (runtime / 'backups').rglob('ca.pem')))
                self.assertIn((runtime / 'certs/ca.pem').read_bytes().strip(), (self.game / 'cacert.pem').read_bytes())
                ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER).load_cert_chain(
                    runtime / 'certs/server.pem', runtime / 'certs/server-key.pem')

    def test_failed_config_publish_restores_originals_and_retry_retains_first_backup(self):
        (self.game / 'stun.ini').unlink()
        original_replace = Path.replace
        failed = False
        def replace(path, destination):
            nonlocal failed
            if Path(destination) == self.game / 'cacert.pem' and not failed:
                failed = True
                raise PermissionError('configuration is locked')
            return original_replace(path, destination)
        with patch.object(Path, 'replace', replace), self.assertRaisesRegex(PermissionError, 'locked'):
            bootstrap.prepare(self.game, self.runtime)
        self.assertEqual((self.game / 'dwauth.ini').read_bytes(), self.original['dwauth.ini'])
        self.assertFalse((self.game / 'stun.ini').exists())
        self.assertEqual((self.game / 'cacert.pem').read_bytes(), self.original['cacert.pem'])
        bootstrap.prepare(self.game, self.runtime)
        bootstrap.prepare(self.game, self.runtime)
        backup = self.runtime / 'backups/client-config'
        self.assertEqual((backup / 'dwauth.ini').read_bytes(), self.original['dwauth.ini'])
        self.assertEqual(json.loads((backup / 'missing.json').read_text()), ['stun.ini'])
        self.assertFalse((backup / 'stun.ini').exists())
        self.assertFalse(list(self.game.glob('*.tmp')))

    def test_unknown_client_fails_before_writing_any_file(self):
        (self.game / 'codoMP_client_shipRetail.exe').write_bytes(b'wrong version')
        before = {p: p.read_bytes() for p in self.game.iterdir()}
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            bootstrap.prepare(self.game, self.runtime)
        self.assertFalse(self.runtime.exists())
        self.assertEqual(before, {p: p.read_bytes() for p in self.game.iterdir()})

    @unittest.skipUnless(os.environ.get('CODOL_TEST_GAME_ROOT'), 'explicit original client required')
    def test_real_prepare_script_initializes_fresh_instance_with_existing_map(self):
        root = Path(__file__).resolve().parents[5]
        source = Path(os.environ['CODOL_TEST_GAME_ROOT']) / 'codoMP_client_shipRetail.exe'
        shutil.copyfile(source, self.game / source.name)
        script = root / 'games/codol/versions/v3_3_3_3/scripts/Prepare-Client.ps1'
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
            str(script), '-PythonPath', sys.executable], env={**os.environ, 'CODOL_REPO_ROOT': str(root),
            'CODOL_GAME_ROOT': str(self.game), 'CODOL_RUNTIME': str(self.runtime)}, capture_output=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertIn(b'ready', result.stdout)
        self.assertIn((self.runtime / 'certs/ca.pem').read_bytes().strip(), (self.game / 'cacert.pem').read_bytes())
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(),
                         hashlib.sha256((self.game / source.name).read_bytes()).digest())


if __name__ == '__main__':
    unittest.main()
