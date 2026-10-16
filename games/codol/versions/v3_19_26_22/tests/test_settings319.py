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
            self.assertEqual(settings.apply_options(runtime), '+set cg_fov 60 +set com_maxfps 0 +set 3291 0 '
                '+set r_fullscreen 0 +set r_mode 1280x720 +set r_customWidth 1280 +set r_customHeight 720')
            self.assertEqual(json.loads(profile.read_text()), {**original, 'name': 'New_Name'})
            backups = list((runtime / 'backups').glob('profile319-*.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(json.loads(backups[0].read_text()), original)
            settings.apply_options(runtime)
            self.assertEqual(list((runtime / 'backups').glob('profile319-*.json')), backups)

    def test_legacy_settings_read_with_display_defaults_without_rewriting(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            path = runtime / 'launch-settings.json'
            legacy = b'{"player_name":"Existing","fov":105,"max_fps":144}'
            path.write_bytes(legacy)
            self.assertEqual(settings.read_options(runtime), {'player_name': 'Existing', 'fov': 105,
                'max_fps': 144, 'display_mode': 'windowed', 'resolution': '1280x720', 'game_language': 'en'})
            self.assertEqual(path.read_bytes(), legacy)

    def test_saved_display_settings_reach_the_game_command(self):
        with tempfile.TemporaryDirectory() as directory:
            runtime = Path(directory)
            for mode, resolution, expected in (
                ('fullscreen', '1920x1080', '+set r_fullscreen 1 +set r_mode 1920x1080 '
                    '+set r_customWidth 1920 +set r_customHeight 1080'),
                ('windowed', '1600x900', '+set r_fullscreen 0 +set r_mode 1600x900 '
                    '+set r_customWidth 1600 +set r_customHeight 900'),
            ):
                with self.subTest(mode=mode):
                    options = {'player_name': 'Player', 'fov': 120, 'max_fps': 400,
                               'display_mode': mode, 'resolution': resolution}
                    settings.save_options(runtime, options)
                    self.assertEqual(settings.read_options(runtime), {**options, 'game_language': 'en'})
                    command = settings.apply_options(runtime)
                    self.assertEqual(command, '+set cg_fov 120 +set com_maxfps 400 +set 3291 0 ' + expected)
                    # Native loader reads CODOL319_EXTRA_ARGS into a 256-byte buffer.
                    self.assertLess(len(command.encode('ascii')), 256)

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
