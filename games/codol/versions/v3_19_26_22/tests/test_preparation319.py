"""Preparing an installation must preserve the selected game and existing progress."""
import hashlib
import os
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import preparation, settings


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game, self.runtime, self.generated = [self.root / n for n in ('original', 'instance', 'generated')]
        for name, data in {'codoMP_client_shipRetail.exe': b'client', 'localization.txt': b'Chinese',
                           'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs': b'original resource',
                           'players/save.dat': b'save', 'Cross/overlay.dll': b'overlay'}.items():
            self.write(self.game / name, data)
        for name, data in {'patches/localization.txt': b'English',
                           'patches/ff_init_common_gfx_V109.ifs': b'patched resource',
                           'publisher-files/configs_s.info': b'generated config',
                           'profile319.json': b'never import player data'}.items():
            self.write(self.generated / name, data)
        self.system = self.root / 'system-version.dll'
        self.system.write_bytes(b'system dll')
        self.hash_patch = patch.object(preparation, 'CLIENT_SHA256', hashlib.sha256(b'client').hexdigest())
        self.hash_patch.start()
        self.addCleanup(self.hash_patch.stop)
        self.native_patch = patch.object(preparation.native_build, 'build', side_effect=self.build_native)
        self.native = self.native_patch.start()
        self.addCleanup(self.native_patch.stop)
        self.boot_patch = patch.object(preparation.boot_assets, 'build', return_value=self.generated)
        self.boot = self.boot_patch.start()
        self.addCleanup(self.boot_patch.stop)

    def build_native(self, target):
        for name, data in {'version.dll': b'proxy', 'client_loopback319.dll': b'bridge',
                           'collision319.exe': b'collision', 'ifs-read.exe': b'reader'}.items():
            self.write(target/name, data)
        return target

    @staticmethod
    def write(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def prepare(self):
        return preparation.prepare(self.game, self.runtime, self.system)

    def test_copy_patches_only_isolated_game_and_preserves_progress_on_repeat(self):
        before = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        game = self.prepare()
        self.assertEqual(game, self.runtime / 'game')
        self.assertEqual((game / 'localization.txt').read_bytes(), b'English')
        self.assertEqual((game / 'localization.txt.original').read_bytes(), b'Chinese')
        self.assertEqual((game / 'version_system319.dll').read_bytes(), b'system dll')
        self.assertFalse((game / 'Cross').exists())
        self.assertFalse((self.runtime / 'server/profile319.json').exists())
        self.assertEqual((self.runtime/'server/publisher-files/configs_s.info').read_bytes(), b'generated config')
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
        self.native.side_effect = FileNotFoundError('compiler missing')
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertFalse((self.runtime/'game').exists())

    def test_preparation_builds_dependencies_without_a_startup_package(self):
        self.assertEqual(self.prepare(), self.runtime / 'game')
        self.native.assert_called_once_with(self.runtime/'server/match-host')
        self.boot.assert_called_once_with(self.game, self.runtime/'generated/boot319', self.runtime/'server/match-host')

    def test_language_round_trip_preserves_original_resources_and_progress(self):
        before = {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        game = self.prepare()
        progress = self.runtime / 'server/profile319.json'
        progress.write_bytes(b'{"name":"Player","experience":12345,"extra":[7]}')
        (game / 'players/save.dat').write_bytes(b'current save')
        originals = {'localization.txt': b'Chinese',
                     'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs': b'original resource'}
        english = {'localization.txt': b'English',
                   'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs': b'patched resource'}
        for language, expected in (('zh-CN', originals), ('en', english), ('zh-CN', originals)):
            with self.subTest(language=language):
                settings.save_options(self.runtime, {'player_name': 'Player', 'fov': 90,
                    'max_fps': 0, 'game_language': language})
                self.prepare()
                for relative, data in expected.items():
                    self.assertEqual((game / relative).read_bytes(), data)
                    self.assertEqual((game / (relative + '.original')).read_bytes(), originals[relative])
                self.assertEqual(progress.read_bytes(), b'{"name":"Player","experience":12345,"extra":[7]}')
                self.assertEqual((game / 'players/save.dat').read_bytes(), b'current save')
        self.assertEqual(before, {p.relative_to(self.game): p.read_bytes() for p in self.game.rglob('*') if p.is_file()})

    def test_first_chinese_language_launch_needs_only_original_language_resources(self):
        for name in ('localization.txt', 'ff_init_common_gfx_V109.ifs'):
            (self.generated / 'patches' / name).unlink()
        settings.save_options(self.runtime, {'player_name': 'Player', 'fov': 90,
            'max_fps': 0, 'game_language': 'zh-CN'})
        game = self.prepare()
        self.assertEqual((game / 'localization.txt').read_bytes(), b'Chinese')
        self.assertEqual((game / 'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs').read_bytes(), b'original resource')

    def test_missing_selected_language_resource_stops_before_changing_copy(self):
        game = self.prepare()
        settings.save_options(self.runtime, {'player_name': 'Player', 'fov': 90,
            'max_fps': 0, 'game_language': 'zh-CN'})
        (self.game / 'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs').unlink()
        before = {p.relative_to(game): p.read_bytes() for p in game.rglob('*') if p.is_file()}
        with self.assertRaises(FileNotFoundError):
            self.prepare()
        self.assertEqual(before, {p.relative_to(game): p.read_bytes() for p in game.rglob('*') if p.is_file()})

    def test_changed_generated_downloads_are_refreshed_without_resetting_profile(self):
        self.prepare()
        profile = self.runtime/'server/profile319.json'
        profile.write_bytes(b'{"experience":12345}')
        self.write(self.generated/'publisher-files/configs_s.info', b'new generated config')
        self.prepare()
        self.assertEqual((self.runtime/'server/publisher-files/configs_s.info').read_bytes(), b'new generated config')
        self.assertEqual(profile.read_bytes(),b'{"experience":12345}')

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
