import json
from pathlib import Path
import tempfile
import unittest

from games.codol.versions.v3_19_26_22.client import settings


class SettingsTests(unittest.TestCase):
    def test_launch_applies_validated_options_without_resetting_progress(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            profile = runtime / 'server/profile319.json'
            profile.parent.mkdir()
            original = {'name': 'OldName', 'rank': 17, 'experience': 95123, 'prestige': 1, 'other': [7]}
            profile.write_text(json.dumps(original), encoding='utf-8')
            self.assertEqual(settings.read_options(runtime)['player_name'], 'OldName')
            settings.save_options(runtime, {'player_name': 'New_Name', 'fov': 60, 'max_fps': 0})
            self.assertEqual(settings.apply_options(runtime), '+set cg_fov 60 +set com_maxfps 0')
            self.assertEqual(json.loads(profile.read_text()), {**original, 'name': 'New_Name'})
            backups = list((runtime / 'backups').glob('profile319-*.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(json.loads(backups[0].read_text()), original)
            settings.apply_options(runtime)
            self.assertEqual(list((runtime / 'backups').glob('profile319-*.json')), backups)

    def test_invalid_saved_options_leave_existing_profile_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            profile = runtime / 'server/profile319.json'
            profile.parent.mkdir()
            profile.write_bytes(b'{"name":"Player","experience":123}')
            (runtime / 'launch-settings.json').write_text('{"player_name":"Valid","fov":90,"max_fps":"0 +quit"}')
            with self.assertRaises(ValueError):
                settings.apply_options(runtime)
            self.assertEqual(profile.read_bytes(), b'{"name":"Player","experience":123}')
