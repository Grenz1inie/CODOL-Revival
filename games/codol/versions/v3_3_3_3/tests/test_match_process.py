# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real JSONL child lifecycle; never launch the production match executable."""
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from games.codol.versions.v3_3_3_3.server.match_server import process


CHILD = r'''
import json, os, sys, time
mode = sys.argv[1]
def emit(event, **fields):
    print(json.dumps(dict(event=event, **fields)), flush=True)
if mode == 'crash_before_ready':
    print('fixture startup failure', file=sys.stderr, flush=True)
    sys.exit(7)
if mode == 'no_ready':
    for line in sys.stdin:
        pass
    sys.exit(0)
if mode == 'invalid_ready':
    emit('ready', port=0, map='mp_nuked', checksum=123456)
    for line in sys.stdin:
        pass
    sys.exit(0)
time.sleep(.03)
emit('ready', port=32123, map='mp_nuked', checksum=123456)
print('fixture stderr', file=sys.stderr, flush=True)
if mode == 'ignore_eof':
    time.sleep(30)
    sys.exit(0)
pending = []
for line in sys.stdin:
    request = json.loads(line)
    if request['op'] == 'stop':
        break
    emit('observed', uid=request['uid'], sid=request['sid'], key=request['key'],
         nested={'sid': request['sid'], 'key': request['key'], 'keep': 1},
         valid=(len(request['sid']) == 16 and len(request['key']) == 32))
    if mode == 'crash':
        os._exit(9)
    if mode == 'invalid_json':
        print('not-json:' + request['key'], flush=True)
        continue
    if mode == 'eof':
        os.close(sys.stdout.fileno())
        time.sleep(30)
    if mode == 'pending':
        continue
    if mode == 'reverse':
        pending.append(request)
        if len(pending) == 2:
            emit('reserved', id=99999, port=32123)
            for r in reversed(pending):
                if r['uid'] == 1:
                    emit('error', id=r['id'], error='reservation rejected')
                else:
                    emit('reserved', id=r['id'], port=32123)
        continue
    emit('reserved', id=request['id'], port=32123)
'''


class NativeMatchProcessTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.children, self.launches = [], []
        self.mode = 'normal'
        real_popen = subprocess.Popen

        def fixture_child(args, **kwargs):
            self.launches.append((args, kwargs.copy()))
            child = real_popen([sys.executable, '-u', '-c', CHILD, self.mode], **kwargs)
            self.children.append(child)
            self.addCleanup(self.reap, child)
            return child

        for target, value in (('ROOT', self.root), ('RUNTIME', self.root / 'runtime'), ('READY_TIMEOUT', 2.),
                              ('RESPONSE_TIMEOUT', 2.), ('CLOSE_TIMEOUT', .2)):
            patcher = patch.object(process, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(process.subprocess, 'Popen', side_effect=fixture_child)
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def reap(child):
        if child.poll() is None:
            child.kill()
        child.wait(timeout=3)
        for stream in (child.stdin, child.stdout):
            if stream is not None:
                stream.close()

    def launch(self, record=None):
        child = process.NativeMatchProcess(self.root / 'package', port=0, record=record)
        self.addCleanup(child.close)
        return child

    def test_ready_reservation_events_and_graceful_owned_shutdown(self):
        events = queue.Queue()
        child = self.launch(lambda event, **fields: events.put((event, fields)))
        self.assertEqual((child.port, child.map_name, child.netconst_checksum),
                         (32123, 'mp_nuked', 123456))
        self.assertEqual(child.pid, self.children[0].pid)
        self.assertTrue(child.is_alive())
        self.assertEqual(child.reserve(42, b'12345678', b'0123456789abcdef'), 32123)
        event, fields = events.get(timeout=1)
        self.assertEqual(event, 'observed')
        self.assertEqual(fields, dict(uid=42, nested={'keep': 1}, valid=True))
        args, options = self.launches[0]
        self.assertEqual(args, [str(self.root / 'runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe'),
                               'serve', '--package', str(self.root / 'package'), '--port', '0'])
        self.assertEqual(options['cwd'], self.root)
        if os.name == 'nt':
            self.assertTrue(options['creationflags'] & subprocess.CREATE_NO_WINDOW)
        child.close()
        child.close()
        self.assertFalse(child.is_alive())
        self.assertEqual(self.children[0].returncode, 0)
        stderr = (self.root / 'runtime/logs/match-rust.stderr.log').read_text()
        self.assertIn('fixture stderr', stderr)
        self.assertNotIn(b'12345678'.hex(), stderr)
        self.assertNotIn(b'0123456789abcdef'.hex(), stderr)
        with self.assertRaises(RuntimeError):
            child.reserve(42, b'12345678', bytes(16))

    def test_startup_crash_invalid_ready_and_timeout_reap_owned_children(self):
        for mode, error in [('crash_before_ready', RuntimeError),
                            ('invalid_ready', RuntimeError), ('no_ready', TimeoutError)]:
            with self.subTest(mode=mode):
                self.mode = mode
                with patch.object(process, 'READY_TIMEOUT', .3):
                    with self.assertRaises(error):
                        self.launch()
                self.assertIsNotNone(self.children[-1].poll())
                self.assertTrue(self.children[-1].stdin.closed)
                self.assertTrue(self.children[-1].stdout.closed)

    def test_crash_eof_and_invalid_json_release_waiting_reservation(self):
        for mode in ('crash', 'eof', 'invalid_json'):
            with self.subTest(mode=mode):
                self.mode = mode
                child = self.launch()
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pending = pool.submit(child.reserve, 42, b'12345678', bytes(16))
                    with self.assertRaises(RuntimeError) as error:
                        pending.result(timeout=1)
                    self.assertNotIn(bytes(16).hex(), str(error.exception))
                self.assertFalse(child.is_alive())
                if mode == 'eof':
                    # Losing stdout must release the request even while alive.
                    self.assertIsNone(self.children[-1].poll())
                child.close()
                self.assertIsNotNone(self.children[-1].poll())

    def test_concurrent_reservations_match_ids_not_response_order(self):
        self.mode = 'reverse'
        child = self.launch()
        with ThreadPoolExecutor(max_workers=2) as pool:
            rejected = pool.submit(child.reserve, 1, b'12345678', bytes(16))
            accepted = pool.submit(child.reserve, 2, b'12345678', bytes(16))
            self.assertEqual(accepted.result(timeout=1), 32123)
            with self.assertRaisesRegex(RuntimeError, 'rejected'):
                rejected.result(timeout=1)
        self.assertTrue(child.is_alive())

    def test_close_unblocks_all_pending_and_gracefully_reaps_child(self):
        self.mode = 'pending'
        requests = queue.Queue()
        child = self.launch(lambda event, **fields: requests.put(event))
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = [pool.submit(child.reserve, uid, b'12345678', bytes(16)) for uid in (1, 2)]
            self.assertEqual(requests.get(timeout=1), 'observed')
            self.assertEqual(requests.get(timeout=1), 'observed')
            child.close()
            for request in pending:
                with self.assertRaisesRegex(RuntimeError, 'closed'):
                    request.result(timeout=1)
        self.assertEqual(self.children[-1].returncode, 0)

    def test_forced_shutdown_does_not_touch_another_owned_instance(self):
        healthy = self.launch()
        self.mode = 'ignore_eof'
        stuck = self.launch()
        stuck.close()
        self.assertFalse(stuck.is_alive())
        self.assertIsNotNone(self.children[-1].returncode)
        self.assertNotEqual(self.children[-1].returncode, 0)
        self.assertTrue(healthy.is_alive())
        self.assertEqual(healthy.reserve(42, b'12345678', bytes(16)), 32123)

    def test_invalid_reservation_material_never_reaches_child(self):
        events = queue.Queue()
        child = self.launch(lambda event, **fields: events.put(event))
        for owner, sid, key in [(0, bytes(8), bytes(16)), (True, bytes(8), bytes(16)),
                                (1 << 64, bytes(8), bytes(16)), (1, bytes(7), bytes(16)),
                                (1, bytes(8), bytes(15)), (1, '12345678', bytes(16))]:
            with self.assertRaises(ValueError):
                child.reserve(owner, sid, key)
        self.assertEqual(child.reserve(42, bytes(8), bytes(16)), 32123)
        self.assertEqual(events.get(timeout=1), 'observed')
        self.assertTrue(events.empty())

    def test_absent_executable_does_not_fall_back_to_python(self):
        with patch.object(process.subprocess, 'Popen', side_effect=FileNotFoundError('missing native executable')) as start:
            with self.assertRaises(FileNotFoundError):
                self.launch()
        self.assertEqual(start.call_count, 1)
        self.assertTrue(start.call_args.kwargs['stderr'].closed)
        self.assertEqual(self.children, [])

    def test_record_exception_does_not_block_control_response(self):
        def bad_record(*_args, **_fields):
            raise ValueError('fixture callback failure')
        child = self.launch(bad_record)
        self.assertEqual(child.reserve(42, bytes(8), bytes(16)), 32123)
