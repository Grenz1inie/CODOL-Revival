"""Control API contract: temp state/docs, no game processes or real saves."""
import json
import subprocess
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from controller import create_server
from dw_marketplace import MarketplaceStore


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'docs/wiki').mkdir(parents=True)
        (self.root / 'docs/wiki/角色.md').write_text('# 角色\n测试正文', encoding='utf-8')
        (self.root / 'docs/report.json').write_text('{"result": 1}', encoding='utf-8')
        (self.root / 'secret.txt').write_text('outside docs', encoding='utf-8')
        self.running = False
        self.server = create_server(self.root, port=0, game_status=lambda: self.running)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f'http://127.0.0.1:{self.server.server_port}'

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()

    def call(self, path, data=None, **headers):
        headers['Content-Type'] = 'application/json'
        request = Request(self.url + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        with urlopen(request) as response:
            return json.load(response)

    def test_skip_defaults_true_and_persists_without_changing_other_state(self):
        self.assertEqual(self.call('/api/settings'), {'skip_tutorial': True})
        self.call('/api/settings', {'skip_tutorial': False})
        self.assertEqual(self.call('/api/settings'), {'skip_tutorial': False})
        saved = json.loads((self.root / 'runtime/data/controller.json').read_text())
        self.assertEqual(saved, {'skip_tutorial': False})
        for bad in [{'skip_tutorial': 'false'}, {'skip_tutorial': 1}, {'unknown': True}]:
            with self.subTest(bad=bad), self.assertRaises(HTTPError) as caught:
                self.call('/api/settings', bad)
            self.assertEqual(caught.exception.code, 400)
        self.assertEqual(self.call('/api/settings'), {'skip_tutorial': False})

    def test_server_status_is_read_only_and_standalone_actions_are_removed(self):
        state = {'running': True, 'pid': 123, 'ready': True, 'ports': []}
        with patch('controller.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(state).encode(), b'')) as run:
            self.assertEqual(self.call('/api/server/status'), state)
            self.assertIn(str(self.root / 'scripts/Control-Services.ps1'), run.call_args.args[0])
        with patch('controller.subprocess.run') as run:
            for path, data in [('/api/server/start', {}), ('/api/server/stop', {}), ('/api/server/status', {})]:
                with self.subTest(path=path), self.assertRaises(HTTPError) as caught:
                    self.call(path, data)
                self.assertEqual(caught.exception.code, 404)
        run.assert_not_called()

    def test_game_actions_use_session_script_and_confirm_observed_state(self):
        for action in ('launch', 'stop'):
            self.running = action == 'stop'
            def execute(command, **kwargs):
                self.assertIn(str(self.root / 'scripts/Control-Game.ps1'), command)
                self.assertEqual(command[command.index('-Action') + 1], 'start' if action == 'launch' else 'stop')
                self.running = action == 'launch'
                return subprocess.CompletedProcess(command, 0, b'', b'')
            with self.subTest(action=action), patch('controller.subprocess.run', side_effect=execute):
                self.assertIn('message', self.call('/api/game/' + action, {}))
                self.assertEqual(self.call('/api/status')['game_running'], action == 'launch')

    def test_stop_without_game_still_cleans_server_and_cleanup_failure_is_reported(self):
        with patch('controller.subprocess.run', return_value=subprocess.CompletedProcess([], 0, b'', b'')) as run:
            self.call('/api/game/stop', {})
            self.assertIn('stop', run.call_args.args[0])
        with patch('controller.subprocess.run', return_value=subprocess.CompletedProcess([], 1, b'', b'Server still running')):
            with self.assertRaises(HTTPError) as caught:
                self.call('/api/game/stop', {})
            self.assertEqual(caught.exception.code, 500)

    def test_game_action_failures_never_report_success(self):
        for action in ('launch', 'stop'):
            self.running = action == 'stop'
            for result in [subprocess.CompletedProcess([], 1, b'', b'UAC cancelled'),
                           subprocess.CompletedProcess([], 0, b'', b''),
                           subprocess.TimeoutExpired('powershell.exe', 120)]:
                with self.subTest(action=action,result=result), patch('controller.subprocess.run') as run:
                    if isinstance(result, Exception): run.side_effect = result
                    else: run.return_value = result
                    with self.assertRaises(HTTPError) as caught:
                        self.call('/api/game/' + action, {})
                    self.assertEqual(caught.exception.code, 500)

    def test_game_actions_reject_get_cross_origin_and_process_arguments(self):
        with patch('controller.subprocess.run') as run:
            for action in ('launch', 'stop'):
                for data, headers, code in [(None, {}, 404), ({'pid': 123}, {}, 400), ({}, {'Origin':'https://example.com'},403)]:
                    with self.subTest(action=action,data=data), self.assertRaises(HTTPError) as caught:
                        self.call('/api/game/' + action, data, **headers)
                    self.assertEqual(caught.exception.code, code)
        run.assert_not_called()

    def test_story_unlock_api_rejects_live_game_and_preserves_other_profile_fields(self):
        from dw_progression import PrivateProfileStore
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        uid = 'e94a180c65d3c23b'
        (directory / (uid + '.bin')).write_bytes((Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes())
        store = PrivateProfileStore(self.root / 'runtime/data/private-profiles', self.root / 'runtime/backups/private-profiles')
        store.set_progression(int(uid, 16), 70, 3)
        before = store.load(int(uid, 16))
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/story', {'user_id': uid})
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(store.load(int(uid, 16)), before)
        self.running = False
        result = self.call('/api/profile/story', {'user_id': uid})
        self.assertEqual(result['story_prerequisites_unlocked'], 10)
        self.assertEqual(store.summary(int(uid, 16)), {'level': 70, 'prestige': 3})
        after = store.load(int(uid, 16))
        for bad in [{'user_id': '../outside'}, {'user_id': uid, 'all': True}]:
            with self.assertRaises(HTTPError) as caught:
                self.call('/api/profile/story', bad)
            self.assertEqual(caught.exception.code, 400)
        self.assertEqual(store.load(int(uid, 16)), after)

    def test_wiki_preserves_paths_and_reads_unicode_and_json(self):
        paths = [entry['path'] for entry in self.call('/api/docs')['files']]
        self.assertEqual(paths, ['report.json', 'wiki/角色.md'])
        result = self.call('/api/docs/file?path=wiki%2F%E8%A7%92%E8%89%B2.md')
        self.assertEqual(result['content'], '# 角色\n测试正文')
        self.assertEqual(self.call('/api/docs/file?path=report.json')['content'], '{"result": 1}')

    def test_outside_docs_and_cross_origin_writes_are_rejected(self):
        for path in ['../secret.txt', '%2e%2e%2fsecret.txt', 'C%3A%2FWindows%2Fwin.ini']:
            with self.subTest(path=path), self.assertRaises(HTTPError) as caught:
                self.call('/api/docs/file?path=' + path)
            self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/settings', {'skip_tutorial': False}, Origin='https://example.com')
        self.assertEqual(caught.exception.code, 403)
        self.assertEqual(self.call('/api/settings'), {'skip_tutorial': True})

    def test_status_reports_available_profiles_and_unsupported_mutations_do_not_write(self):
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        sample = Path(__file__).parent / 'fixtures/public-profile.bin'
        target = directory / 'e94a180c65d3c23b.bin'
        target.write_bytes(sample.read_bytes())
        status = self.call('/api/status')
        self.assertEqual(status['profiles'][0]['user_id'], 'e94a180c65d3c23b')
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/unknown', {'user_id': 'e94a180c65d3c23b'})
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(target.read_bytes(), sample.read_bytes())

    def test_currency_api_persists_rejects_invalid_accounts_and_running_game(self):
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        sample = (Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes()
        (directory / 'e94a180c65d3c23b.bin').write_bytes(sample)
        data = {'user_id': 'e94a180c65d3c23b', 'amount': 100}
        result = self.call('/api/profile/currency', data)
        self.assertEqual(result['currency'], 100)
        self.assertEqual(self.call('/api/status')['profiles'][0]['currency'], 100)
        for bad in [{**data, 'amount': True}, {**data, 'amount': -1},
                    {**data, 'user_id': '../outside'}, {**data, 'extra': 1}]:
            with self.subTest(bad=bad), self.assertRaises(HTTPError) as caught:
                self.call('/api/profile/currency', bad)
            self.assertEqual(caught.exception.code, 400)
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/currency', {**data, 'user_id': '0000000000000001'})
        self.assertEqual(caught.exception.code, 404)
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/currency', data)
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(self.call('/api/status')['profiles'][0]['currency'], 100)
        self.assertEqual((directory / 'e94a180c65d3c23b.bin').read_bytes(), sample)

    def test_invalid_saved_currency_is_reported_without_overwriting_it(self):
        directory = self.root / 'runtime/data/marketplace'
        directory.mkdir(parents=True)
        (directory / 'e94a180c65d3c23b.json').write_text('{}', encoding='utf-8')
        profiles = self.root / 'runtime/data/public-profiles'
        profiles.mkdir(parents=True)
        (profiles / 'e94a180c65d3c23b.bin').write_bytes((Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes())
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/currency', {'user_id': 'e94a180c65d3c23b', 'amount': 10})
        self.assertEqual(caught.exception.code, 400)
        self.assertEqual((directory / 'e94a180c65d3c23b.json').read_text(), '{}')

    def test_premium_api_is_separate_and_rejects_live_game_writes(self):
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        (directory / 'e94a180c65d3c23b.bin').write_bytes((Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes())
        data = {'user_id': 'e94a180c65d3c23b', 'amount': 1000}
        self.assertEqual(self.call('/api/profile/premium', data)['premium'], 1000)
        profile = self.call('/api/status')['profiles'][0]
        self.assertEqual((profile['premium'], profile['currency']), (1000, 0))
        for bad in [True, -1, 2147483647]:
            with self.assertRaises(HTTPError) as caught:
                self.call('/api/profile/premium', {**data, 'amount': bad})
            self.assertEqual(caught.exception.code, 400)
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/premium', data)
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(self.call('/api/status')['profiles'][0]['premium'], 1000)

    def test_inventory_listing_and_manual_renewal_obey_account_and_running_boundaries(self):
        uid = 'e94a180c65d3c23b'
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        (directory / (uid + '.bin')).write_bytes((Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes())
        store = MarketplaceStore(self.root / 'runtime/data/marketplace', self.root / 'runtime/backups/marketplace')
        store.add_currency(int(uid, 16), 20000)
        store.purchase(int(uid, 16), 848, unlock_rank=370)
        old = store.inventory(int(uid, 16))[0]['expires']
        result = self.call('/api/profile/renew', {'user_id': uid, 'item_id': 1429, 'days': 30})
        self.assertEqual(result['expires'], old + 2592000)
        items = self.call('/api/inventory?user_id=' + uid)['items']
        self.assertEqual(items[0]['item_id'], 1429)
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/renew', {'user_id': uid, 'item_id': 1429, 'days': 30})
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual(store.inventory(int(uid, 16))[0]['expires'], old + 2592000)

    def test_grant_all_api_is_offline_and_preserves_public_profile(self):
        uid = 'e94a180c65d3c23b'
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        original = (Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes()
        (directory / (uid + '.bin')).write_bytes(original)
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/unlock', {'user_id': uid})
        self.assertEqual(caught.exception.code, 409)
        self.running = False
        result = self.call('/api/profile/unlock', {'user_id': uid})
        self.assertEqual(result['granted'], 6772)
        self.assertEqual(len(self.call('/api/inventory?user_id=' + uid)['items']), 6772)
        self.assertEqual((directory / (uid + '.bin')).read_bytes(), original)

    def test_progression_api_applies_verified_maximum_and_protects_existing_public_profile(self):
        directory = self.root / 'runtime/data/public-profiles'
        directory.mkdir(parents=True)
        original = (Path(__file__).parent / 'fixtures/public-profile.bin').read_bytes()
        (directory / 'e94a180c65d3c23b.bin').write_bytes(original)
        data = {'user_id': 'e94a180c65d3c23b', 'level': 70, 'prestige': 3}
        result = self.call('/api/profile/progression', data)
        self.assertEqual((result['level'], result['prestige']), (70, 3))
        profile = self.call('/api/status')['profiles'][0]
        self.assertEqual((profile['level'], profile['prestige']), (70, 3))
        for bad in [{**data, 'level': 71}, {**data, 'prestige': 4}, {**data, 'level': True},
                    {**data, 'user_id': '../outside'}, {**data, 'extra': 1}]:
            with self.subTest(bad=bad), self.assertRaises(HTTPError) as caught:
                self.call('/api/profile/progression', bad)
            self.assertEqual(caught.exception.code, 400)
        self.running = True
        with self.assertRaises(HTTPError) as caught:
            self.call('/api/profile/progression', data)
        self.assertEqual(caught.exception.code, 409)
        self.assertEqual((directory / 'e94a180c65d3c23b.bin').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
