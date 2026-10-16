"""Directory selection and control gates through the real local HTTP interface."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from controller import create_server
from manager.installations import Installations


class ManagerApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / '游戏目录'
        (self.game / 'IIPS').mkdir(parents=True)
        (self.game / 'IIPS/IIPSVersion.ini').write_text('3.3.3.3')
        (self.game / 'client.exe').write_bytes(b'client')
        self.manager = Installations(self.root, catalog=[{'game_id': 'codol', 'version': '3.3.3.3',
            'adapter': 'games.codol.versions.v3_3_3_3.adapter', 'executable': 'client.exe',
            'sha256': hashlib.sha256(b'client').hexdigest()}])
        self.running = False
        self.choice = None
        self.server = create_server(self.root, 0, game_status=lambda: self.running,
                                    installations=self.manager, choose_directory=lambda: self.choice)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def call(self, path, data=None, **headers):
        request = Request(self.url + '/api/' + path, headers={'Content-Type': 'application/json', **headers},
                          data=None if data is None else json.dumps(data).encode())
        with urlopen(request) as response:
            return json.load(response)

    def test_unmatched_cannot_launch_or_write_and_versions_are_available(self):
        self.assertEqual(self.call('status')['installation']['state'], 'unselected')
        self.assertEqual(self.call('versions')['versions'][0]['version'], '3.3.3.3')
        for endpoint, body in [('game/launch', {}), ('settings', {'skip_tutorial': False}),
                               ('profile/currency', {'user_id': '0000000000000001', 'amount': 10})]:
            with self.subTest(endpoint=endpoint), patch('controller.subprocess.run') as run:
                with self.assertRaises(HTTPError) as error: self.call(endpoint, body)
                self.assertEqual(error.exception.code, 409)
                run.assert_not_called()

    def test_choose_cancel_match_invalid_and_running_switch(self):
        self.assertTrue(self.call('installation/choose', {})['cancelled'])
        self.assertFalse(self.manager.file.exists())
        self.choice = str(self.game)
        result = self.call('installation/choose', {})
        self.assertEqual(result['installation']['state'], 'matched')
        self.assertTrue(self.call('status')['capabilities']['launch']['available'])
        self.choice = None
        self.assertTrue(self.call('installation/choose', {})['cancelled'])
        self.assertEqual(self.manager.current()['state'], 'matched')
        self.running = True
        with self.assertRaises(HTTPError) as error: self.call('installation/select', {'path': str(self.root)})
        self.assertEqual(error.exception.code, 409)
        self.running = False
        self.call('installation/select', {'path': str(self.root)})
        self.assertEqual(self.call('status')['capabilities'], {})

    def test_launch_routes_to_selected_code_and_runtime_and_revalidates(self):
        selected = self.call('installation/select', {'path': str(self.game)})['installation']
        def launch(command, **options):
            self.assertIn('v3_3_3_3', ' '.join(command))
            self.assertEqual(options['env']['CODOL_GAME_ROOT'], str(self.game))
            self.assertEqual(options['env']['CODOL_RUNTIME'], str(self.manager.runtime(selected)))
            self.running = True
            return subprocess.CompletedProcess(command, 0, b'', b'')
        with patch('controller.subprocess.run', side_effect=launch):
            self.call('game/launch', {})
        self.running = False
        (self.game / 'client.exe').write_bytes(b'unknown client')
        with patch('controller.subprocess.run') as run:
            with self.assertRaises(HTTPError) as error: self.call('game/launch', {})
            self.assertEqual(error.exception.code, 409)
            run.assert_not_called()

    def test_selection_api_rejects_foreign_origin_and_extra_fields(self):
        for body, headers, code in [({'path': str(self.game)}, {'Origin': 'https://example.com'}, 403),
                                    ({'path': str(self.game), 'adapter': 'evil'}, {}, 400)]:
            with self.assertRaises(HTTPError) as error: self.call('installation/select', body, **headers)
            self.assertEqual(error.exception.code, code)

    def test_version_capabilities_are_enforced_by_backend(self):
        self.call('installation/select', {'path': str(self.game)})
        from games.codol.versions.v3_3_3_3.adapter import Adapter
        with patch.dict(Adapter.capabilities, {'launch': {'available': False}, 'skip_tutorial': {'available': False}}):
            for endpoint, body in [('game/launch', {}), ('settings', {'skip_tutorial': False})]:
                with self.subTest(endpoint=endpoint), patch('controller.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as run:
                    with self.assertRaises(HTTPError) as error: self.call(endpoint, body)
                    self.assertEqual(error.exception.code, 409)
                    run.assert_not_called()

    def test_running_server_blocks_switch_and_session_can_stop_changed_client(self):
        selected = self.call('installation/select', {'path': str(self.game)})['installation']
        with patch('controller.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'{"running":true}', b'')):
            with self.assertRaises(HTTPError) as error: self.call('installation/select', {'path': str(self.root)})
            self.assertEqual(error.exception.code, 409)
        (self.root / 'config/session.json').write_text(json.dumps(selected), encoding='utf-8')
        (self.game / 'client.exe').write_bytes(b'changed')
        self.running = True
        def stop(command, **options):
            self.assertEqual(command[-3], 'stop')
            self.assertEqual(options['env']['CODOL_RUNTIME'], str(self.manager.runtime(selected)))
            self.running = False
            return subprocess.CompletedProcess(command, 0, b'', b'')
        with patch('controller.subprocess.run', side_effect=stop): self.call('game/stop', {})
        self.assertFalse((self.root / 'config/session.json').exists())
