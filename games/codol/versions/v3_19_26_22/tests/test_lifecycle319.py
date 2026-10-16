"""Service lifecycle through real disposable loopback processes."""
from pathlib import Path
import socket
import json
import psutil
import sys
import tempfile
import time
import unittest

from games.codol.versions.v3_19_26_22.client.lifecycle import Services, lobby_ready


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.runtime = Path(self.tmp.name) / 'runtime'

    def spec(self, name, *, fail=False):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        code = 'raise SystemExit(7)' if fail else (
            "import socket,time; s=socket.socket(); s.bind(('127.0.0.1',%d)); s.listen(); time.sleep(60)" % port)
        return {'name': name, 'port': port, 'command': [sys.executable, '-c', code]}

    def test_start_reports_only_owned_listeners_and_stop_reaps_children(self):
        services = Services(self.runtime, [self.spec('auth'), self.spec('lobby')])
        self.addCleanup(services.close)
        services.start(timeout=5)
        state = services.status()
        self.assertTrue(state['running'])
        self.assertTrue(state['ready'])
        self.assertTrue(all(p['listening'] and not p['conflict'] for p in state['ports']))
        services.close()
        self.assertFalse(services.status()['running'])
        self.assertFalse(services.status()['ready'])

    def test_foreign_listener_is_not_stopped_and_no_partial_start_occurs(self):
        spec = self.spec('occupied')
        with socket.socket() as foreign:
            foreign.bind(('127.0.0.1', spec['port']))
            foreign.listen()
            services = Services(self.runtime, [self.spec('unused'), spec])
            self.addCleanup(services.close)
            with self.assertRaisesRegex(OSError, str(spec['port'])):
                services.start(timeout=1)
            self.assertFalse(services.status()['running'])
            self.assertFalse(self.runtime.exists())
            with socket.create_connection(('127.0.0.1', spec['port']), timeout=1):
                pass

    def test_failed_start_cleans_up_services_already_created(self):
        services = Services(self.runtime, [self.spec('auth'), self.spec('broken', fail=True)])
        self.addCleanup(services.close)
        with self.assertRaisesRegex(RuntimeError, 'broken'):
            services.start(timeout=5)
        self.assertFalse(services.status()['running'])

    def test_udp_readiness_requires_own_bound_socket_and_preserves_foreign_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as reserved:
            reserved.bind(('127.0.0.1', 0))
            port = reserved.getsockname()[1]
        spec = {'name': 'match', 'port': port, 'protocol': 'UDP', 'command': [sys.executable, '-c',
            "import socket,time; s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); "
            f"s.bind(('127.0.0.1',{port})); time.sleep(60)"]}
        services = Services(self.runtime, [spec])
        self.addCleanup(services.close)
        services.start(timeout=2)
        self.assertEqual(services.status()['ports'], [
            {'name': 'match', 'protocol': 'UDP', 'port': port, 'listening': True, 'conflict': False}])
        services.close()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as foreign:
            foreign.bind(('127.0.0.1', port))
            other = Services(self.runtime, [spec])
            self.addCleanup(other.close)
            with self.assertRaisesRegex(OSError, str(port)):
                other.start(timeout=2)
            self.assertFalse(other.status()['running'])
            foreign.getsockname()

    def test_forced_stop_reaps_owned_helper_processes(self):
        spec = self.spec('parent')
        pidfile = Path(self.tmp.name) / 'child.json'
        spec['command'] = [sys.executable, '-c',
            'import subprocess,sys,socket,time,json; from pathlib import Path; '
            "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
            f'Path({str(pidfile)!r}).write_text(json.dumps(p.pid)); '
            f"s=socket.socket(); s.bind(('127.0.0.1',{spec['port']})); s.listen(); time.sleep(60)"]
        services = Services(self.runtime, [spec])
        services.start()
        child = psutil.Process(json.loads(pidfile.read_text()))
        try:
            services.close()
            self.assertFalse(child.is_running())
        finally:
            services.close()
            if child.is_running():
                child.kill()
                child.wait(timeout=5)

    def test_only_current_launch_profile_event_proves_lobby_connection(self):
        log = Path(self.tmp.name) / 'lobby.jsonl'
        since = time.time()
        self.assertFalse(lobby_ready(log, since))
        log.write_text('{"event":"secure_profile_read","time":1}\n')
        self.assertFalse(lobby_ready(log, since))
        with log.open('a') as out:
            out.write('{"event":"secure_profile_read","time":%s}\n{"incomplete"' % (since + 1))
        self.assertTrue(lobby_ready(log, since))


if __name__ == '__main__':
    unittest.main()
