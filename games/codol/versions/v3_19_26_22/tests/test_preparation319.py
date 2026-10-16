"""Preparing an installation must preserve the selected game and existing progress."""
import hashlib
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import preparation


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game, self.runtime, self.package = [self.root / n for n in ('original', 'instance', 'package')]
        for name, data in {'codoMP_client_shipRetail.exe': b'client', 'localization.txt': b'Chinese',
                           'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs': b'original resource',
                           'players/save.dat': b'save', 'Cross/overlay.dll': b'overlay'}.items():
            self.write(self.game / name, data)
        for name, data in {'patches/localization.txt': b'English',
                           'patches/ff_init_common_gfx_V109.ifs': b'patched resource',
                           'server/match-host/version.dll': b'proxy',
                           'server/match-host/client_loopback319.dll': b'loopback',
                           'server/loader/Client-english-fixed-resources.exe': b'loader',
                           'server/profile319.json': b'{"rank":1,"experience":0}',
                           'server/local-profiles319/economy319.json': b'{}'}.items():
            self.write(self.package / name, data)
        self.system = self.root / 'system-version.dll'
        self.system.write_bytes(b'system dll')
        self.hash_patch = patch.object(preparation, 'CLIENT_SHA256', hashlib.sha256(b'client').hexdigest())
        self.hash_patch.start()
        self.addCleanup(self.hash_patch.stop)

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def prepare(self):
        return preparation.prepare(self.game, self.runtime, self.package, self.system)

    def test_copy_patches_only_isolated_game_and_preserves_progress_on_repeat(self):
        before = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        game = self.prepare()
        self.assertEqual(game, self.runtime / 'game')
        self.assertEqual((game / 'localization.txt').read_bytes(), b'English')
        self.assertEqual((game / 'localization.txt.original').read_bytes(), b'Chinese')
        self.assertEqual((game / 'version_system319.dll').read_bytes(), b'system dll')
        self.assertFalse((game / 'Cross').exists())
        self.assertEqual((game / 'codol319-root.txt').read_text().strip(), str(self.runtime / 'server/match-host') + '\\')
        (game / 'players/save.dat').write_bytes(b'new save')
        (self.runtime / 'server/profile319.json').write_text('{"experience":100}')
        self.prepare()
        self.assertEqual((game / 'players/save.dat').read_bytes(), b'new save')
        self.assertEqual((self.runtime / 'server/profile319.json').read_text(), '{"experience":100}')
        self.assertEqual(before, {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob('*') if p.is_file()})

    def test_wrong_client_or_missing_dependency_fails_before_copy(self):
        (self.game / preparation.CLIENT).write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError, '指纹'):
            self.prepare()
        self.assertFalse(self.runtime.exists())
        (self.game / preparation.CLIENT).write_bytes(b'client')
        (self.package / 'server/match-host/version.dll').unlink()
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertFalse(self.runtime.exists())

    def test_import_retains_assets_without_copying_reference_service_code(self):
        self.write(self.package / 'server/start319.py', b'not our entrypoint')
        destination = self.root / 'imported'
        hashes = {p: hashlib.sha256((self.package / p).read_bytes()).hexdigest()
                  for p in preparation.NATIVE_HASHES}
        with patch.dict(preparation.NATIVE_HASHES, hashes, clear=True):
            preparation.import_package(self.package, destination)
            self.assertFalse((destination / 'server/start319.py').exists())
            self.assertEqual((destination / 'server/profile319.json').read_bytes(), b'{"rank":1,"experience":0}')
            self.write(self.package / 'server/match-host/version.dll', b'changed')
            with self.assertRaisesRegex(ValueError, '指纹'):
                preparation.import_package(self.package, self.root / 'bad-import')
            self.assertFalse((self.root / 'bad-import').exists())

    def test_low_space_is_checked_on_destination_volume_before_copy(self):
        from collections import namedtuple
        usage = namedtuple('usage', 'total used free')(100, 99, 1)
        with patch('shutil.disk_usage', return_value=usage) as check:
            with self.assertRaisesRegex(OSError, '空间'):
                self.prepare()
            self.assertEqual(check.call_args.args[0], self.root)
        self.assertFalse((self.runtime / 'game').exists())

    def test_interrupted_copy_is_completed_before_it_can_be_used(self):
        self.write(self.runtime / 'game' / preparation.CLIENT, b'client')
        game = self.prepare()
        self.assertEqual((game / 'players/save.dat').read_bytes(), b'save')

    @unittest.skipUnless(os.name == 'nt', 'Windows elevated session access')
    def test_runtime_explicitly_grants_current_user_inherited_access(self):
        self.prepare()
        script = '''$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User;
        $acl=[IO.Directory]::GetAccessControl($env:TEST_RUNTIME);
        $rules=@($acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier]) | Where-Object {
            $_.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -eq $sid.Value -and
            $_.InheritanceFlags -eq 'ContainerInherit, ObjectInherit' -and
            ($_.FileSystemRights -band [Security.AccessControl.FileSystemRights]::Modify) -eq [Security.AccessControl.FileSystemRights]::Modify
        }); if(!$rules.Count){exit 1}'''
        result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', script],
            env={**os.environ, 'TEST_RUNTIME': str(self.runtime)}, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))

    @unittest.skipUnless(os.name == 'nt', 'Windows file access')
    def test_existing_log_gets_current_user_access_without_directory_inheritance_flags(self):
        log = self.root / 'existing.log'
        log.write_text('diagnostic')
        preparation.grant_runtime_access(log)
        script = '''$sid=[Security.Principal.WindowsIdentity]::GetCurrent().User;
        $acl=[IO.File]::GetAccessControl($env:TEST_LOG);
        $rules=@($acl.GetAccessRules($true,$false,[Security.Principal.SecurityIdentifier]) | Where-Object {
            $_.IdentityReference.Value -eq $sid.Value -and $_.InheritanceFlags -eq 'None'
        }); if(!$rules.Count){exit 1}'''
        result = subprocess.run(['powershell.exe', '-NoProfile', '-Command', script],
            env={**os.environ, 'TEST_LOG': str(log)}, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))


if __name__ == '__main__':
    unittest.main()
