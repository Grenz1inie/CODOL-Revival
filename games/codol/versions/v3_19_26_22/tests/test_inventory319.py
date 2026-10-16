"""3.19 inventory contracts: native consumption, not an encoder round trip."""
import importlib.util
import hashlib
import hmac
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.server import console_store


SERVER = Path(__file__).resolve().parents[1] / 'server'


def load_profile(root):
    spec = importlib.util.spec_from_file_location('inventory_profile319', SERVER / 'local_profile319.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(os.environ, CODOL319_SERVER_ROOT=str(root)), patch.dict(sys.modules, console_store=console_store):
        spec.loader.exec_module(module)
    return module


class InventoryFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / 'local-profiles319'
        self.data.mkdir()
        (self.data / 'wallet.json').write_text('{"1":2100,"2":57}')
        self.profile = load_profile(self.root)


class Inventory319Tests(InventoryFixture):
    def test_assets_reply_is_one_composite_result_even_for_empty_inventory(self):
        reply = self.profile.player_assets_reply(230, 9)
        expected = (b'\x0a' + struct.pack('<Q', 9) + b'\x08' + bytes(4) + b'\x03\xe6'
                    + b'\x08\x01\0\0\0' * 2)
        self.assertEqual(reply[:26], expected)
        self.assertEqual(reply[26:37], b'\x0a' + struct.pack('<Q', 1000001) + b'\x10\0')
        self.assertEqual(reply[-10:], b'\x08' + bytes(4) + b'\x08' + bytes(4))

    def test_standalone_inventory_uses_account_owner_and_permanent_sentinels(self):
        item = self.profile.inventory_item(114, keyed=True)
        self.assertEqual(item[:11], b'\x0a' + struct.pack('<Q', 1000001) + b'\x10\0')
        self.assertEqual(struct.unpack_from('<I', item, 33)[0], 0xffffffff)
        self.assertEqual(struct.unpack_from('<q', item, 38)[0], 0x7fffffffffffffff)
        self.assertEqual(struct.unpack_from('<I', item, 50)[0], 0xffffffff)


class NativeInventory319Tests(InventoryFixture):
    @classmethod
    def setUpClass(cls):
        try:
            from client_inventory319 import InventoryReader319
            cls.reader = InventoryReader319()
        except (FileNotFoundError, ImportError) as error:
            raise unittest.SkipTest('Captured 3.19 native reader unavailable: ' + str(error))

    def test_client_consumes_complete_registry_with_inherited_owner_and_wallet(self):
        ids = list(range(100, 21840))
        (self.data / 'owned_items.json').write_text(json.dumps(ids))
        before = (self.data / 'owned_items.json').read_bytes()
        payload = self.profile.player_assets_reply(230, 9)[26:]
        result = self.reader.parse(payload)
        self.assertEqual((result['ok'], result['consumed'], result['count'], result['logs']),
                         (1, len(payload), len(ids), 0))
        for index in (0, 19999, 20000, len(ids)-1):
            self.assertEqual(self.reader.item(result['items'] + index*0xb8), {
                'owner': 1000001, 'id': ids[index], 'quantity': 1, 'experience': 0,
                'expiry': 0xffffffff, 'usage': 0x7fffffffffffffff,
                'expiry_duration': 0xffffffff, 'status': 0})
        cpu, obj = self.reader.cpu, self.reader.object
        self.assertEqual(self.reader.u32(obj+0x40), 2)
        self.assertEqual(bytes(cpu.mem_read(obj+0x88, 1)), b'\x01')
        self.assertEqual(self.reader.u32(obj+0x8c), 2100)
        self.assertEqual(bytes(cpu.mem_read(obj+0xd8, 1)), b'\x02')
        self.assertEqual(self.reader.u32(obj+0xdc), 57)
        self.assertEqual((self.data / 'owned_items.json').read_bytes(), before)

    def test_client_consumes_empty_inventory_and_rejects_truncated_or_wrong_tags(self):
        empty = self.profile.player_assets_reply(230, 1)[26:]
        self.assertEqual(self.reader.parse(empty)['ok'], 1)
        (self.data / 'owned_items.json').write_text('[114]')
        data = self.profile.player_assets_reply(230, 2)[26:]
        self.assertEqual(self.reader.parse(data)['ok'], 1)
        for broken in (data[:-1], data[:-5], data[:36], b'\x08'+data[1:]):
            with self.subTest(length=len(broken), first=broken[:1]):
                self.assertEqual(self.reader.parse(broken)['ok'], 0)


class LobbyInventory319Tests(InventoryFixture):
    def test_login_task_230_reads_persisted_items_through_real_lobby_dispatch(self):
        (self.data / 'owned_items.json').write_text('[114,31403]')
        # Only the test listener's port changes. Execute the production handshake/dispatch.
        script = '''
import runpy, socket
class TestSocket(socket.socket):
    def bind(self, address): super().bind(('127.0.0.1', 0))
    def listen(self, count):
        super().listen(count)
        print(self.getsockname()[1], flush=True)
socket.socket = TestSocket
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
        spec = importlib.util.spec_from_file_location('inventory_codec319', SERVER / 'lsg_codec.py')
        codec = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(codec)
        with socket.create_connection(('127.0.0.1', port), timeout=5) as connection:
            def exact(count):
                data = b''
                while len(data) < count:
                    chunk = connection.recv(count-len(data))
                    self.assertTrue(chunk, 'Lobby closed before replying')
                    data += chunk
                return data
            def frame():
                head = exact(4)
                return head + exact(struct.unpack('<I', head)[0])
            hello = struct.pack('<4I', 200, 200, 210, 220) + bytes(12)
            connection.sendall(hello)
            greeting = frame()
            auth = b'\xab\x82' + b'isolated-test'
            framed = struct.pack('<I', len(auth)+8) + auth
            prk = hmac.new(hashlib.sha1(hello[8:]+greeting+framed).digest(),
                           b'Local319DiagnosticKey123', hashlib.sha1).digest()
            challenges = hmac.new(prk, b'CLIENTCHAL\x01', hashlib.sha1).digest()[:16]
            connection.sendall(framed + challenges[:8])
            self.assertEqual(frame()[4:], b'\xab\x83' + challenges[8:])
            keys, previous = b'', b''
            for i in range(1, 5):
                previous = hmac.new(prk, previous+b'BDDATA'+bytes([i]), hashlib.sha1).digest()
                keys += previous
            client_keys = keys[20:40]+keys[:20]+keys[56:72]+keys[40:56]
            self.assertEqual(codec.decode(frame()[4:], client_keys)[0], 4)
            connection.sendall(codec.encode(0x86, b'\x50\x03\xe6\x10\0\0', client_keys, 1))
            kind, reply = codec.decode(frame()[4:], client_keys)
            self.assertEqual(kind, 1)
            self.assertEqual(reply[14:16], b'\x03\xe6')
            self.assertEqual(struct.unpack_from('<I', reply, 17)[0], 1,
                             'Login must receive one player-assets result, not empty success')
            self.assertEqual(reply, self.profile.player_assets_reply(230, 1))


if __name__ == '__main__':
    unittest.main()
