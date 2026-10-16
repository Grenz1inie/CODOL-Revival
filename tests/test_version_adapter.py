"""The version adapter owns profile formats, process inputs and runtime data."""
import importlib
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class VersionAdapterTests(unittest.TestCase):
    def test_selected_version_owns_data_code_and_launch_environment(self):
        module = importlib.import_module('games.codol.versions.v3_3_3_3.adapter')
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            selection = {'path': str(repo / '游戏 A'), 'version': '3.3.3.3', 'instance_id': 'a'}
            runtime = repo / 'runtime/instances/a'
            adapter = module.Adapter(repo, selection, runtime)
            self.assertEqual(adapter.settings(), {'skip_tutorial': True})
            adapter.set_settings({'skip_tutorial': False})
            self.assertEqual(adapter.settings(), {'skip_tutorial': False})
            other = module.Adapter(repo, {**selection, 'instance_id': 'b'}, repo / 'runtime/instances/b')
            self.assertEqual(other.settings(), {'skip_tutorial': True})
            self.assertEqual(adapter.environment()['CODOL_GAME_ROOT'], selection['path'])
            self.assertEqual(adapter.environment()['CODOL_RUNTIME'], str(runtime))
            self.assertIn('v3_3_3_3', adapter.environment()['CODOL_VERSION_ROOT'])
            self.assertEqual(adapter.profiles(), [])
            directory = runtime / 'data/public-profiles'
            directory.mkdir(parents=True)
            fixture = ROOT / 'tests/fixtures/public-profile.bin'
            if not fixture.exists():
                fixture = ROOT / 'games/codol/versions/v3_3_3_3/tests/fixtures/public-profile.bin'
            shutil.copyfile(fixture, directory / '0000000000000001.bin')
            adapter.mutate('currency', {'user_id': '0000000000000001', 'amount': 19})
            self.assertEqual(adapter.profiles()[0]['currency'], 19)
            self.assertEqual(other.profiles(), [])
            self.assertFalse((repo / 'runtime/data').exists())
