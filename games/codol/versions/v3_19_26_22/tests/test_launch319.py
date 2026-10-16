import json
import hashlib
import os
from pathlib import Path
import tempfile
import socket
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from games.codol.versions.v3_19_26_22.client import launch, preparation, settings
from games.codol.versions.v3_19_26_22.client.lifecycle import Services


class LaunchTests(unittest.TestCase):
    def test_supervisor_passes_display_settings_without_forcing_720p_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            (runtime / 'game').mkdir()
            (runtime / 'game' / preparation.CLIENT).write_bytes(b'client')
            settings.save_options(runtime, {'player_name': 'Player', 'fov': 90, 'max_fps': 144,
                'display_mode': 'fullscreen', 'resolution': '2560x1440'})
            spawned = []

            def spawn(command, **kwargs):
                process = Mock(pid=100 + len(spawned))
                process.poll.return_value = 0 if command[0].endswith('.exe') and 'Client-' in command[0] else None
                spawned.append((command, kwargs))
                return process

            connections = [SimpleNamespace(laddr=SimpleNamespace(ip='127.0.0.1', port=port),
                pid=100 + i, status='LISTEN') for i, port in enumerate((31900, 31901, 8319))]
            with patch.object(preparation, 'CLIENT_SHA256', hashlib.sha256(b'client').hexdigest()), \
                    patch.object(launch, 'NATIVE_HASHES', {}), patch('socket.socket'), \
                    patch('psutil.net_connections', return_value=connections), \
                    patch('psutil.Process') as process_info, patch('subprocess.Popen', side_effect=spawn):
                process_info.return_value.create_time.return_value = 1.0
                process_info.return_value.children.return_value = []
                launch.supervise(runtime)
            command, arguments = spawned[-1]
            self.assertTrue(command[0].endswith(preparation.LOADER.replace('/', os.sep)))
            self.assertNotIn('--windowed', command)
            self.assertEqual(arguments['env']['CODOL319_EXTRA_ARGS'],
                '+set cg_fov 90 +set com_maxfps 144 +set 3291 0 +set r_fullscreen 1 '
                '+set r_mode 2560x1440 +set r_customWidth 2560 +set r_customHeight 1440')
            self.assertIn('游戏在登录前退出', launch.read(runtime)['error'])

    def test_match_status_reports_own_udp_and_preserves_lobby_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime = Path(tmp)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            services = Services(runtime, [{'name':'match', 'protocol':'UDP', 'port':port,
                'command':[sys.executable, '-c', 'import socket,time; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); '
                    f"s.bind(('127.0.0.1',{port})); time.sleep(30)"]}])
            try:
                services.start()
                current = launch.identity(os.getpid())
                launch.save(runtime, {'phase':'lobby', 'supervisor':current, 'game':current, 'services':[],
                    'match':{'phase':'running', 'error':'', 'service':services.records[0]}})
                state = launch.status(runtime)
                self.assertTrue(state['lobby_ready'])
                self.assertTrue(state['match']['ready'])
                self.assertEqual(state['ports'][0]['protocol'], 'UDP')
                services.close()
                self.assertFalse(launch.status(runtime)['match']['ready'])
            finally:
                services.close()

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
