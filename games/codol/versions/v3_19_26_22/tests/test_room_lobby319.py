"""Production lobby dispatch and Rust admissions over an isolated TCP listener."""
import hashlib
import hmac
import os
import socket
import struct
import subprocess
import sys

from games.codol.versions.v3_19_26_22.server import lsg_codec, room319
from test_inventory319 import InventoryFixture, SERVER
from test_room319 import SEARCH, FIXTURES, FIRST_BROADCAST, READY_BROADCAST, channel_message


class RoomLobby319Tests(InventoryFixture):
    def test_lobby_routes_native_host_state_to_rust_and_pushes_seventeen_admissions(self):
        script = '''
import runpy, socket, sys
class TestSocket(socket.socket):
    def bind(self, address): super().bind(('127.0.0.1', 0))
    def listen(self, count):
        super().listen(count)
        print(self.getsockname()[1], flush=True)
socket.socket = TestSocket
sys.argv.append('--ayria-parity')
runpy.run_path('lsg_handshake.py', run_name='__main__')
'''
        process = subprocess.Popen([sys.executable, '-B', '-c', script], cwd=SERVER,
            env={**os.environ, 'CODOL319_SERVER_ROOT': str(self.root)},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(process.stdout.close)
        self.addCleanup(process.stderr.close)
        def stop():
            process.terminate()
            process.wait(timeout=5)
        self.addCleanup(stop)
        port = int(process.stdout.readline())
        with socket.create_connection(('127.0.0.1', port), timeout=5) as connection:
            def exact(count):
                result = b''
                while len(result) < count:
                    data = connection.recv(count - len(result))
                    self.assertTrue(data, 'lobby closed before reply')
                    result += data
                return result
            def frame():
                head = exact(4)
                return head + exact(struct.unpack('<I', head)[0])
            hello = struct.pack('<4I', 200, 200, 210, 220) + bytes(12)
            connection.sendall(hello)
            greeting = frame()
            auth = b'\xab\x82room-isolated-test'
            framed = struct.pack('<I', len(auth) + 8) + auth
            prk = hmac.new(hashlib.sha1(hello[8:] + greeting + framed).digest(),
                           b'Local319DiagnosticKey123', hashlib.sha1).digest()
            challenges = hmac.new(prk, b'CLIENTCHAL\x01', hashlib.sha1).digest()[:16]
            connection.sendall(framed + challenges[:8])
            self.assertEqual(frame()[4:], b'\xab\x83' + challenges[8:])
            keys, previous = b'', b''
            for i in range(1, 5):
                previous = hmac.new(prk, previous + b'BDDATA' + bytes([i]), hashlib.sha1).digest()
                keys += previous
            keys = keys[20:40] + keys[:20] + keys[56:72] + keys[40:56]
            self.assertEqual(lsg_codec.decode(frame()[4:], keys)[0], 4)
            sequence = 1
            def receive(kind):
                nonlocal sequence
                wire = frame()[4:]
                sequence += 1
                self.assertEqual(struct.unpack_from('<I', wire, 2)[0], sequence)
                actual, body = lsg_codec.decode(wire, keys)
                self.assertEqual(actual, kind)
                return body
            def request(body, transaction):
                connection.sendall(lsg_codec.encode(0x86, body, keys, transaction))
                return receive(1)
            request(SEARCH, 1)
            created = request(b'\x0b\x03\x0d', 2)
            self.assertEqual(struct.unpack_from('<I', created, 17)[0], 1)
            channel = struct.unpack_from('<Q', created, 27)[0]
            request(FIRST_BROADCAST, 3)
            members = [receive(2) for _ in range(17)]
            self.assertEqual([struct.unpack_from('<Q', p, 6)[0] for p in members],
                             list(range(0x600000001, 0x600000012)))
            self.assertTrue(all(struct.unpack_from('<I', p, 1)[0] == 9 for p in members))
            bot = {'uid': 0x600000001, 'name': 'Bot01'}
            self.assertEqual(receive(2), room319.message_event(channel, bot, b'\x1a\0'))
            request(channel_message(channel, (FIXTURES / 'roster-native.bin').read_bytes()), 4)
            joins = [receive(2) for _ in range(17)]
            self.assertEqual([struct.unpack_from('<Q', p, 6)[0] for p in joins],
                             list(range(0x600000001, 0x600000012)))
            self.assertTrue(all(struct.unpack_from('<I', p, 1)[0] == 7 for p in joins))
            self.assertEqual(receive(2), room319.message_event(channel, bot, b'\x1a\0'))
            # Repeated host state must not inject the same bots a second time.
            request(channel_message(channel, (FIXTURES / 'roster-native.bin').read_bytes()), 5)
            request(READY_BROADCAST, 6)
            owner = {'uid': 1000001, 'name': 'LocalPlayer'}
            self.assertEqual(receive(2), room319.message_event(channel, owner, b'\x20\x02'))
            connection.settimeout(0.1)
            with self.assertRaises(TimeoutError):
                connection.recv(1)
