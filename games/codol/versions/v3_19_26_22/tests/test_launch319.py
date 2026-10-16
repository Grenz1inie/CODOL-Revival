import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import launch


class LaunchTests(unittest.TestCase):
    def test_missing_or_stale_session_does_not_claim_game_or_server_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            self.assertFalse(launch.status(runtime)['running'])
            (runtime / 'startup.json').write_text(json.dumps({'phase': 'lobby',
                'supervisor': {'pid': 99999999, 'created': 0}, 'services': [],
                'game': {'pid': 99999998, 'created': 0}}))
            state = launch.status(runtime)
            self.assertFalse(state['running'])
            self.assertFalse(state['lobby_ready'])
            self.assertFalse(state['ready'])
            launch.stop(runtime)

    def test_uac_rejection_is_reported_without_starting_game(self):
        with patch('ctypes.windll.shell32.ShellExecuteW', return_value=5):
            with self.assertRaisesRegex(OSError, 'UAC'):
                launch.elevate(Path('C:/codol/runtime'))

    def test_live_game_is_started_while_first_run_dialog_waits_for_user(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            current = launch.identity(os.getpid())
            (runtime / 'startup.json').write_text(json.dumps({'phase': 'launching',
                'supervisor': current, 'game': current, 'services': []}))
            state = launch.status(runtime)
            self.assertTrue(state['game_running'])
            self.assertFalse(state['lobby_ready'])
            with patch.object(launch, 'prepare'), patch.object(launch, 'elevate'), patch.object(launch, 'save'), \
                    patch.object(launch, 'status', side_effect=[{'running': False}, state]):
                launch.start(runtime / 'original', runtime)
