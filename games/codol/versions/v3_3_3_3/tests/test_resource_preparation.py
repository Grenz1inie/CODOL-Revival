"""First-run resource inputs and publication, independent of research artifacts."""
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
import zlib

VERSION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERSION / 'reverse/tools'))
from reference_match.navigation import Navigation


class ResourcePreparationTests(unittest.TestCase):
    def test_export_cannot_escape_the_explicit_staging_root(self):
        from export_match_map import export_zones
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            for output in (root, root / '../escape'):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'output must'):
                    export_zones({}, output, output_root=root)
            self.assertEqual(list(root.iterdir()), [])

    def test_resource_check_reports_invalid_manifest_without_repairing_it(self):
        from games.codol.versions.v3_3_3_3.client.preparation import PACKAGE, resource_errors
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / PACKAGE
            directory.mkdir(parents=True)
            for content in ('{broken', '{"schema_version":2}'):
                (directory / 'manifest.json').write_text(content)
                self.assertIn('Nuketown package unavailable', '\n'.join(resource_errors(root)))
                self.assertEqual((directory / 'manifest.json').read_text(), content)

    def test_resource_check_reports_missing_package_and_server_without_writes(self):
        from games.codol.versions.v3_3_3_3.client.preparation import resource_errors
        with tempfile.TemporaryDirectory() as folder:
            errors = '\n'.join(resource_errors(Path(folder)))
            self.assertIn('Prepare-Resources.ps1', errors)
            self.assertIn('Invoke-MatchCargo.ps1', errors)
            self.assertEqual(list(Path(folder).iterdir()), [])

    @unittest.skipUnless(os.environ.get('CODOL_TEST_GAME_ROOT'), 'requires explicitly selected original game')
    def test_clean_root_generates_complete_package_and_reuses_it(self):
        from games.codol.versions.v3_3_3_3.client.preparation import prepare
        from reference_match.mapdata import load_map
        with tempfile.TemporaryDirectory(prefix='准备 clean ') as folder:
            root = Path(folder)
            original = Path(os.environ['CODOL_TEST_GAME_ROOT'])
            game = root / '原游戏 copy'
            (game / 'IIPS/IIPSDownload').mkdir(parents=True)
            for name in ('codoMP_client_shipRetail.exe', 'IIPS/IFS2.dll'):
                shutil.copyfile(original / name, game / name)
            with self.assertRaisesRegex(FileNotFoundError, 'Missing game archive'):
                prepare(root, game)
            self.assertEqual(list((root / 'runtime/builds/codol/v3_3_3_3/maps').iterdir()), [])
            from extract_story_resources import NUKETOWN_ARCHIVES, digest
            originals = [original / 'IIPS/IIPSDownload' / name for name in NUKETOWN_ARCHIVES]
            before = [digest(path) for path in originals]
            for source in originals:
                shutil.copyfile(source, game / 'IIPS/IIPSDownload' / source.name)
            package = prepare(root, game)
            loaded = load_map(package)
            self.assertTrue(loaded['manifest']['physics_ready'])
            self.assertEqual(loaded['manifest']['map'], 'mp_nuked')
            self.assertEqual(len(loaded['baselines']), 98)
            self.assertEqual(loaded['ncs']['client_checksum'], 1765105316)
            loadout = json.loads(loaded['files']['loadout.json'])
            self.assertEqual([loadout[k]['index'] for k in ('weapon', 'body', 'hands')], [5, 109, 54])
            self.assertFalse((root / 'research').exists())
            stamp = (package / 'manifest.json').stat().st_mtime_ns
            self.assertEqual(prepare(root, game), package)
            self.assertEqual((package / 'manifest.json').stat().st_mtime_ns, stamp)
            binary = os.environ.get('CODOL_TEST_MATCH_EXE')
            if binary:
                with subprocess.Popen([binary, 'serve', '--package', str(package), '--port', '0'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
                    try:
                        # Native server emits readiness after fully loading the package.
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            future = pool.submit(process.stdout.readline)
                            try:
                                line = future.result(timeout=30)
                            finally:
                                process.terminate()
                        self.assertIn(b'ready', line)
                    finally:
                        if process.poll() is None:
                            process.terminate()
                        process.wait(timeout=10)
            weapon = package / 'weapon-acr.bin'
            weapon.write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                prepare(root, game)
            self.assertEqual(weapon.read_bytes(), b'corrupt')
            self.assertEqual((package / 'manifest.json').stat().st_mtime_ns, stamp)
            self.assertEqual([digest(path) for path in originals], before)

    def test_wrong_client_fails_before_creating_runtime(self):
        from games.codol.versions.v3_3_3_3.client.preparation import prepare
        with tempfile.TemporaryDirectory(prefix='准备 empty ') as folder:
            root = Path(folder)
            game = root / 'game'
            game.mkdir()
            (game / 'codoMP_client_shipRetail.exe').write_bytes(b'wrong version')
            with self.assertRaisesRegex(ValueError, 'client hash mismatch'):
                prepare(root, game)
            self.assertFalse((root / 'runtime').exists())

    def test_distributed_inputs_preserve_verified_registration_and_navigation(self):
        resources = VERSION / 'resources'
        registration = json.loads((resources / 'definitions/network-registration423.json').read_text())
        self.assertEqual(registration['checksum_seed'], 3451066449)
        self.assertEqual(zlib.crc32(''.join(registration['names']).encode('ascii')), 3451066449)
        self.assertEqual(registration['exe_sha256'],
                         'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b')
        self.assertNotIn('pid', registration)
        self.assertNotIn('image_base', registration)
        data = (resources / 'navigation/mp_nuked_wp.csv').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'dae775b788537a20e64b72524eecf1847f40f02e7a1070a69687441f77d69807')
        self.assertEqual(len(Navigation.from_csv(data.decode('ascii'), None).nodes), 235)


if __name__ == '__main__':
    unittest.main()
