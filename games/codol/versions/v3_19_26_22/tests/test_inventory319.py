"""3.19 inventory contracts: native consumption, not an encoder round trip."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch

from lobby_client319 import connect_lobby

from games.codol.versions.v3_19_26_22.server import console_store
from games.codol.versions.v3_19_26_22.server import lsg_codec


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
        # These unit fixtures supply their own tables; production publishes this last.
        (self.root / 'common-ready.json').write_text('{}')
        (self.data / 'wallet.json').write_text('{"1":2100,"2":57}')
        self.profile = load_profile(self.root)


class Inventory319Tests(InventoryFixture):
    def test_full_inventory_fits_small_lobby_frame_without_dropping_items(self):
        ids = list(range(100, 21840))
        (self.data / 'owned_items.json').write_text(json.dumps(ids))
        reply = self.profile.player_assets_reply(230, 9)
        # Conservative regression budget, not a claim about the client's exact limit.
        self.assertLessEqual(len(lsg_codec.encode(1, reply, bytes(72), 1)), 65536)
        self.assertEqual(reply[26:28], b'\x16\x08')
        self.assertEqual(struct.unpack_from('<I', reply, 28)[0], 50)
        raw_size = struct.unpack_from('<I', reply, 33)[0]
        packed_size = struct.unpack_from('<I', reply, 38)[0]
        raw = zlib.decompress(reply[42:])
        self.assertEqual((raw_size, packed_size), (len(raw), len(reply)-42))
        self.assertEqual(struct.unpack_from('<I', raw, 31)[0], len(ids))
        self.assertEqual([struct.unpack_from('<I', raw, 36+48*i)[0] for i in range(len(ids))], ids)

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
        self.assertEqual(payload[0], 0x16)
        result = self.reader.parse(payload)
        self.assertEqual((result['ok'], result['consumed'], result['count']),
                         (1, 40+48*len(ids), len(ids)))
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

    def test_native_zlib_wrapper_matches_bytes_and_rejects_corrupt_checksum(self):
        raw = self.profile.player_assets_reply(230, 1)[26:]
        packed = zlib.compress(raw)
        block = b'\x16' + b''.join(b'\x08'+struct.pack('<I', n)
                                  for n in (50, len(raw), len(packed))) + packed
        result = self.reader.parse(block)
        self.assertEqual((result['ok'], result['consumed'], result['count']), (1, len(raw), 0))
        for data, expected in ((packed, 1), (packed[:-1]+bytes([packed[-1]^1]), 0), (packed[:-1], 0)):
            reader = self.reader
            reader.cpu.mem_write(reader.data, data)
            reader.write32(reader.buffer, reader.data+0x10000)
            reader.write32(reader.buffer+4, reader.data)
            self.assertEqual(reader.call(0xb75ed0, reader.buffer,
                             reader.buffer, len(raw), reader.buffer+4, len(data)), expected)
            if expected:
                self.assertEqual(bytes(reader.cpu.mem_read(reader.data+0x10000, len(raw))), raw)

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
        (self.data / 'owned_items.json').write_text(json.dumps(list(range(100, 21840))))
        request = connect_lobby(self, self.root)
        reply = request(b'\x50\x03\xe6\x10\0\0')
        self.assertEqual(reply[14:16], b'\x03\xe6')
        self.assertEqual(struct.unpack_from('<I', reply, 17)[0], 1,
                         'Login must receive one player-assets result, not empty success')
        self.assertEqual(reply, self.profile.player_assets_reply(230, 1))



if __name__ == '__main__':
    unittest.main()
