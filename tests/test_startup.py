"""Startup preflight uses disposable files, never the player's runtime or game."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_startup', ROOT / 'games/codol/versions/v3_3_3_3/client/checks.py')
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)


class StartupFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codol startup ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'CODOL Revival 测试'
        self.game = self.root.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z'
        for name in ('games/codol/versions/v3_3_3_3/server/local_server.py', 'src/controller.py', 'games/codol/versions/v3_3_3_3/scripts/Start-Services.ps1',
                     'scripts/Start-Controller.ps1', 'games/codol/versions/v3_3_3_3/scripts/Launch-Game.ps1',
                     'games/codol/versions/v3_3_3_3/scripts/Control-Game.ps1', 'games/codol/versions/v3_3_3_3/scripts/Control-Services.ps1', 'games/codol/versions/v3_3_3_3/scripts/Stop-Game.ps1',
                     'games/codol/versions/v3_3_3_3/resources/definitions/marketplace-catalog.json', 'web/dist/index.html'):
            self.write(self.root / name, '{}')
        self.write(self.root / 'web/dist/index.html',
                   '<script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">')
        self.write(self.root / 'web/dist/assets/app.js', '// test')
        self.write(self.root / 'web/dist/assets/app.css', 'body{}')
        self.write(self.root / 'requirements.txt', (ROOT / 'requirements.txt').read_text())
        self.write(self.root / 'runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe', 'not executed')
        self.write(self.game / 'codoMP_client_shipRetail.exe', 'test executable; never started')
        self.write(self.game / 'dwauth.ini', '127.0.0.1 3074\n127.0.0.1 443\n0x03EA\n')
        self.write(self.game / 'stun.ini', '127.0.0.1\n')
        self.make_certificate()

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def make_certificate(self, expired=False):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
        now = datetime.now(timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(days=2))
                .not_valid_after(now + timedelta(days=-1 if expired else 2))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
        pem = cert.public_bytes(serialization.Encoding.PEM).decode()
        for path in (self.root / 'runtime/certs/ca.pem', self.root / 'runtime/certs/server.pem',
                     self.game / 'cacert.pem'):
            self.write(path, pem)
        self.write(self.root / 'runtime/certs/server-key.pem', key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode())


class StartupChecksTests(StartupFixture, unittest.TestCase):
    def test_before_preparation_check_is_read_only_and_needs_no_node_when_ui_is_built(self):
        before = {p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()}
        self.assertEqual(startup.check_environment(self.root, self.game, self.root / 'runtime', include_package=False), [])
        self.assertEqual({p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()}, before)

    def test_default_preflight_reports_missing_package(self):
        errors = '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime'))
        self.assertIn('Prepare-Resources.ps1', errors)

    def test_missing_files_are_reported_together_with_frontend_build_instructions(self):
        for name in ('games/codol/versions/v3_3_3_3/server/local_server.py', 'web/dist/index.html', 'runtime/certs/server.pem',
                     'games/codol/versions/v3_3_3_3/scripts/Control-Game.ps1', 'games/codol/versions/v3_3_3_3/scripts/Control-Services.ps1', 'games/codol/versions/v3_3_3_3/scripts/Stop-Game.ps1'):
            (self.root / name).unlink()
        errors = '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime'))
        for expected in ('local_server.py', 'server.pem', 'npm ci', 'npm run build',
                         'Control-Game.ps1', 'Control-Services.ps1', 'Stop-Game.ps1'):
            self.assertIn(expected, errors)

    def test_incomplete_frontend_assets_are_rejected(self):
        (self.root / 'web/dist/assets/app.js').unlink()
        self.assertIn('app.js', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))

    def test_python_and_dependency_failures_include_repair_commands(self):
        with patch.object(sys, 'version_info', (3, 8, 0)):
            self.assertIn('Python', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))
        with patch.object(startup.metadata, 'version', return_value='0.0'):
            self.assertIn('pip install -r', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))
        with patch.object(startup.metadata, 'version', side_effect=startup.metadata.PackageNotFoundError):
            self.assertIn('cryptography', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))

    def test_wrong_game_endpoints_and_settings_are_rejected_without_repairing_files(self):
        self.write(self.game / 'dwauth.ini', 'example.com 3074\n127.0.0.1 443\n0x03EA')
        self.write(self.game / 'stun.ini', 'example.com')
        self.write(self.root / 'runtime/data/controller.json', '{"skip_tutorial":"false"}')
        errors = '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime'))
        for name in ('dwauth.ini', 'stun.ini', 'skip_tutorial'):
            self.assertIn(name, errors)
        self.assertEqual((self.game / 'stun.ini').read_text(), 'example.com')

    def test_expired_invalid_or_untrusted_certificates_are_rejected(self):
        self.make_certificate(expired=True)
        self.assertIn('expired', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))
        self.make_certificate()
        self.write(self.game / 'cacert.pem', '')
        self.assertIn('cacert.pem', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))
        self.write(self.root / 'runtime/certs/server-key.pem', 'invalid key')
        self.assertIn('certificate', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))

    def test_server_signed_by_another_ca_returns_an_actionable_failure(self):
        original_server = (self.root / 'runtime/certs/server.pem').read_bytes()
        self.make_certificate()
        (self.root / 'runtime/certs/server.pem').write_bytes(original_server)
        self.assertIn('certificate', '\n'.join(startup.check_environment(self.root, self.game, self.root / 'runtime')))
