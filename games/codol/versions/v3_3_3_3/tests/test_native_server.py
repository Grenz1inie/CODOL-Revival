"""Native lifecycle contract; Popen is always replaced, never run the engine."""
import ast
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import zlib

from games.codol.versions.v3_3_3_3.server.native_server import NativeServer


PUBLICATION = 'Calculate referenced files checksums...\nactual_client_crc=1\n'


class NativeServerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name) / 'CODOL-Revival'
        self.stage = self.root / 'research/experiments/story-native'
        self.stage.mkdir(parents=True)
        self.exe = self.stage / 'built.exe'
        self.exe.write_bytes(b'not an executable')
        native = self.root / 'games/codol/versions/v3_3_3_3/reverse/tools/native'
        native.mkdir(parents=True)
        (native / 'server3333.patch').write_bytes(b'patch fixture')
        (native / 'minimal_cargoship.gsc').write_text('main() {}\n')
        self.client = self.root.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        self.client.parent.mkdir()
        self.client.write_bytes(b'client fixture')
        digest = hashlib.sha256(self.client.read_bytes()).hexdigest()
        self.addCleanup(patch.stopall)
        patch('games.codol.versions.v3_3_3_3.server.native_server.CLIENT_SHA256', digest).start()
        self.manifest = dict(executable=str(self.exe),
                             executable_sha256=hashlib.sha256(self.exe.read_bytes()).hexdigest(),
                             patch_sha256=hashlib.sha256(b'patch fixture').hexdigest())
        (self.stage / 'native-build3333.json').write_text(json.dumps(self.manifest))
        reference = self.root.parent / 'CODOL-2.6.9.7-Launcher/CODOL-2.6.9.7-Launcher/runtime/game/server2697'
        (reference / 'script-overlay2697').mkdir(parents=True)
        (reference / 'script-overlay2697/overlay.gsc').write_text('overlay fixture')
        loadout = reference / 'scripts/coop/maps/mp/gametypes/_coopmode.gsc'
        loadout.parent.mkdir(parents=True)
        loadout.write_text('resolveLoadout()\n{ old(); }\ngiveStartingLoadout()\n{ keep(); }\n')
        evidence = self.root / 'research/evidence'
        evidence.mkdir()
        (evidence / 'live-netconst-registration423.json').write_text(json.dumps(dict(
            exe_sha256=digest, names=['one', 'two'], codinfo_names=['one'],
            checksum_seed=zlib.crc32(b'onetwo'))))
        self.options = dict(security_id=bytes.fromhex('1020304050607080'),
                            profile_path=self.root / 'profiles',
                            admission_path=self.root / 'admission.txt',
                            key_path=self.root / 'key.bin')
        self.process = Mock(returncode=None)
        self.process.poll.side_effect = lambda: self.process.returncode
        self.process.terminate.side_effect = lambda: setattr(self.process, 'returncode', 0)
        self.process.wait.side_effect = lambda timeout: self.process.returncode
        self.log = PUBLICATION
        self.exit_on_launch = None
        self.popen = patch('games.codol.versions.v3_3_3_3.server.native_server.subprocess.Popen', side_effect=self.launch).start()
        self.socket = patch('games.codol.versions.v3_3_3_3.server.native_server.socket.socket').start()
        self.elapsed = 0
        patch('games.codol.versions.v3_3_3_3.server.native_server.time.monotonic', side_effect=lambda: self.elapsed).start()
        patch('games.codol.versions.v3_3_3_3.server.native_server.time.sleep', side_effect=self.advance).start()
        self.server = NativeServer(self.root)
        self.addCleanup(self.server.close)

    def advance(self, seconds):
        self.elapsed += seconds

    def launch(self, command, **kwargs):
        self.process.returncode = self.exit_on_launch
        self.home = kwargs['cwd']
        (self.home / 'main').mkdir(exist_ok=True)
        (self.home / 'main/qconsole.log').write_text(self.log)
        return self.process

    def test_start_preserves_preparation_and_passes_connection_material(self):
        self.assertFalse(self.server.ready)
        with patch.dict(os.environ, {'CODOL_ADMISSION_PATH': 'unrelated-roster'}):
            self.assertIs(self.server.start(**self.options), self.server)
        self.assertTrue(self.server.ready)
        self.assertIs(self.server.process, self.process)
        self.assertEqual(self.server.home.parent, self.stage)
        command = self.popen.call_args.args[0]
        settings = dict(zip(command[2:-3:3], command[3:-3:3]))
        for key, value in dict(net_ip='127.0.0.1', net_port='28970',
                               codol_securityId='1020304050607080',
                               codol_securityKeyPath=str(self.options['key_path']),
                               codol_admissionPath=str(self.options['admission_path']),
                               codol_profilePath=str(self.options['profile_path']),
                               codol_admissionRequired='1', codol_target2697='1',
                               codol_sessionMap='coop_training_mp_cargoship').items():
            self.assertEqual(settings[key], value)
        self.assertEqual(command[-3:], ['+map', 'mp_cargoship', '+codol_checktargetpublication'])
        self.assertNotIn('CODOL_ADMISSION_PATH', self.popen.call_args.kwargs['env'])
        guard = self.socket.return_value.__enter__.return_value
        guard.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        guard.bind.assert_called_once_with(('127.0.0.1', 28970))
        loadout = (self.server.home / 'scripts/coop/maps/mp/gametypes/_coopmode.gsc').read_text()
        self.assertIn('level.coop_primary = "defaultweapon_mp";', loadout)
        self.assertIn('giveStartingLoadout()\n{ keep(); }', loadout)
        self.assertEqual((self.server.home / 'scripts/coop/maps/mp/mp_cargoship.gsc').read_text(),
                         'main() {}\n')
        self.assertTrue((self.server.home / 'registration423.txt').read_text().endswith('\none\ntwo\none\n'))
        for name in ('profile_path', 'admission_path', 'key_path'):
            self.assertFalse(self.options[name].exists())
        self.process.returncode = 7
        self.assertFalse(self.server.ready)

    def test_close_reaps_only_owned_child_even_when_termination_times_out(self):
        self.server.start(**self.options)
        idle = NativeServer(self.root)
        idle.close()
        self.process.terminate.side_effect = None
        self.process.wait.side_effect = [subprocess.TimeoutExpired('owned', 10), 0, 0]
        self.process.kill.side_effect = lambda: setattr(self.process, 'returncode', -9)
        self.server.close()
        self.server.close()
        self.assertFalse(self.server.ready)
        self.process.terminate.assert_called_once()
        self.process.kill.assert_called_once()
        self.assertIsNone(idle.process)

    def test_pvp_starts_killhouse_with_one_bot_and_room_for_one_human(self):
        reference = self.root.parent / 'CODOL-2.6.9.7-Launcher/CODOL-2.6.9.7-Launcher/runtime/game/server2697'
        waypoints = reference / 'runtime-assets/main/waypoints'
        waypoints.mkdir(parents=True)
        (waypoints / 'mp_killhouse_sh_wp.csv').write_text('waypoint fixture')
        self.server = NativeServer(self.root, mode='pvp')
        self.addCleanup(self.server.close)
        self.server.start(**self.options)
        command = self.popen.call_args.args[0]
        settings = dict(zip(command[2:-3:3], command[3:-3:3]))
        for key, value in dict(sv_maxclients='2', scr_codol_bots='1', scr_codol_botfill='0',
                               g_gametype='dm', fs_game='', codol_zoneType='mp',
                               codol_sessionMap='', net_ip='127.0.0.1').items():
            self.assertEqual(settings[key], value)
        self.assertEqual(command[-3:], ['+map', 'mp_killhouse_sh', '+codol_checktargetpublication'])
        self.assertEqual((self.server.home / 'main/waypoints/mp_killhouse_sh_wp.csv').read_text(),
                         'waypoint fixture')
        self.assertTrue(self.server.ready)

    def test_timeout_requires_both_publication_markers_and_cleans_up(self):
        for text in ('', 'Calculate referenced files checksums...', 'actual_client_crc=1'):
            with self.subTest(text=text):
                self.log = text
                self.elapsed = 0
                with self.assertRaisesRegex(RuntimeError, 'timeout'):
                    self.server.start(**self.options)
                self.assertEqual(self.elapsed, 40)
                self.assertFalse(self.server.ready)
                self.assertIsNotNone(self.process.returncode)
        self.assertEqual(self.process.terminate.call_count, 3)

    def test_explicit_initialization_failures_win_over_publication(self):
        for text, reason in (
            ('With the reason: Server crashed:', 'server crashed'),
            ('CoDOL native startup archives mounted\nmap mount failed', 'map initialization failed'),
        ):
            with self.subTest(reason=reason):
                self.log = PUBLICATION + text
                with self.assertRaisesRegex(RuntimeError, reason):
                    self.server.start(**self.options)
                self.assertFalse(self.server.ready)
                self.assertIsNotNone(self.process.returncode)

    def test_sys_error_and_early_exit_are_not_readiness(self):
        def fail(command, **kwargs):
            process = self.launch(command, **kwargs)
            (self.home / 'sys_error.txt').write_text('failed')
            return process
        self.popen.side_effect = fail
        with self.assertRaisesRegex(RuntimeError, 'sys_error'):
            self.server.start(**self.options)
        self.process.terminate.assert_called_once()
        self.popen.side_effect = self.launch
        self.exit_on_launch = 23
        with self.assertRaisesRegex(RuntimeError, 'exit 23'):
            self.server.start(**self.options)
        self.process.terminate.assert_called_once()
        self.assertFalse(self.server.ready)

    def test_recoverable_diagnostic_waits_for_publication(self):
        self.log = 'ERROR: recoverable Pathnode diagnostic\n'
        def publish(seconds):
            self.advance(seconds)
            self.assertFalse(self.server.ready)
            (self.home / 'main/qconsole.log').write_text(self.log + PUBLICATION)
        with patch('games.codol.versions.v3_3_3_3.server.native_server.time.sleep', side_effect=publish):
            self.server.start(**self.options)
        self.assertTrue(self.server.ready)
        self.assertGreater(self.elapsed, 0)

    def test_second_start_does_not_replace_or_stop_owned_child(self):
        self.server.start(**self.options)
        with self.assertRaisesRegex(RuntimeError, 'already started'):
            self.server.start(**self.options)
        self.assertTrue(self.server.ready)
        self.popen.assert_called_once()
        self.process.terminate.assert_not_called()

    def test_busy_loopback_port_fails_without_launching_or_stopping_process(self):
        self.socket.return_value.__enter__.return_value.bind.side_effect = OSError('port busy')
        with self.assertRaisesRegex(OSError, 'port busy'):
            self.server.start(**self.options)
        self.server.close()
        self.popen.assert_not_called()
        self.process.terminate.assert_not_called()
        self.assertIsNone(self.server.home)

    def test_interrupted_wait_cleans_up_child(self):
        self.log = ''
        with patch('games.codol.versions.v3_3_3_3.server.native_server.time.sleep', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.server.start(**self.options)
        self.assertFalse(self.server.ready)
        self.process.terminate.assert_called_once()

    def test_spawn_failure_never_stops_an_unowned_process(self):
        self.popen.side_effect = OSError('spawn failed')
        with self.assertRaisesRegex(OSError, 'spawn failed'):
            self.server.start(**self.options)
        self.server.close()
        self.process.terminate.assert_not_called()
        self.assertIsNone(self.server.process)

    def test_hash_mismatches_block_launch(self):
        for path in (self.exe, self.client, self.root / 'games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch'):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaises(AssertionError):
                    self.server.start(**self.options)
                path.write_bytes(original)
        self.popen.assert_not_called()

    def test_probe_reuses_lifecycle_and_keeps_evidence_on_success_and_failure(self):
        probe = Path(__file__).resolve().parents[5] / 'games/codol/versions/v3_3_3_3/reverse/tools/probe_native_server.py'
        # Refuse to import the original top-level launcher in this test.
        tree = ast.parse(probe.read_text())
        self.assertTrue(any(isinstance(node, ast.FunctionDef) and node.name == 'main'
                            for node in tree.body), 'probe needs an import-safe main')
        main = runpy.run_path(str(probe), run_name='probe_test')['main']
        for text, ready in ((PUBLICATION, True), ('', False)):
            with self.subTest(ready=ready), redirect_stdout(io.StringIO()):
                self.log = text
                if ready:
                    main(self.root)
                else:
                    with self.assertRaisesRegex(AssertionError, 'timeout'):
                        main(self.root)
                result = json.loads((self.root / 'research/evidence/server3333-startup-latest.json').read_text())
                self.assertEqual(result['ready'], ready)
                self.assertFalse(result['gameplay_verified'])
                self.assertEqual(result['returncode'], 0)
                self.assertEqual(result['patch_sha256'], self.manifest['patch_sha256'])
                self.assertEqual(json.loads((Path(result['home']) / 'probe.json').read_text()), result)
                command = result['command']
                for key in ('codol_profilePath', 'codol_admissionPath', 'codol_securityKeyPath'):
                    self.assertEqual(command[command.index(key) + 1], '')
        self.assertEqual(self.popen.call_count, 2)

    def test_registration_identity_and_checksum_are_verified_before_launch(self):
        path = self.root / 'research/evidence/live-netconst-registration423.json'
        original = json.loads(path.read_text())
        for key, value in (('exe_sha256', 'wrong'), ('checksum_seed', 0)):
            with self.subTest(key=key):
                path.write_text(json.dumps({**original, key: value}))
                with self.assertRaises(AssertionError):
                    self.server.start(**self.options)
        self.popen.assert_not_called()


if __name__ == '__main__':
    unittest.main()
