"""Local currency mutations and the client-observed marketplace wire seam."""
import json
import hmac
from pathlib import Path
import sys
import struct
import tempfile
import time
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dw_marketplace import MarketplaceStore
from dw_profiles import ProfileStore
from dw_lobby import handle_lobby
from test_dw_lobby import HELLO, MemorySocket, client_auth, request

USER_ID = 0xe94a180c65d3c23b


class CurrencyTests(unittest.TestCase):
    def test_premium_service_93_balance_purchase_and_refresh(self):
        purchase = bytes.fromhex('10000801000000080100000008010000000801000000010008010000000a00000000000000001000080000000008000000000300080000000000')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 1000, currency_id=2)
            auth, _, keys = client_auth()
            tasks = [(8, 1, bytes.fromhex('0a3bc2d3650c184ae900')),
                     (93, 1, bytes.fromhex('080100000000')), (93, 131, purchase),
                     (93, 1, bytes.fromhex('080100000000'))]
            sock = MemorySocket(HELLO + auth + b''.join(request(keys, service=s, task=t, sequence=n+1, parameters=p)
                                                       for n, (s, t, p) in enumerate(tasks)))
            events = []
            handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                         lambda *_: 'memory', profiles=ProfileStore(root / 'profiles'), marketplace=store)
            self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))
            balances = []
            for reply in (sock.sent[3], sock.sent[5]):
                aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(reply[10:26])).decryptor()
                clear = aes.update(reply[26:-8]) + aes.finalize()
                balances.append(clear[31:38])
            self.assertEqual(balances, [bytes.fromhex('030208e8030000'), bytes.fromhex('030208f7000000')])
            self.assertEqual(store.balance(USER_ID, currency_id=2), 247)
            self.assertEqual(store.balance(USER_ID), 0)
            self.assertEqual(store.inventory(USER_ID)[0]['item_id'], 100)

    def test_grant_all_includes_non_shop_attachments_and_skins_without_charging_or_stacking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 10000)
            store.add_currency(USER_ID, 20000, currency_id=2)
            store.purchase(USER_ID, 3386)
            store.grant_all(USER_ID)
            restored = MarketplaceStore(root / 'data', root / 'backups')
            items = restored.inventory(USER_ID)
            self.assertEqual(len(items), 6772)
            self.assertEqual(len({x['item_id'] for x in items}), 6772)
            self.assertTrue(all(x['quantity'] == 1 and x['expires'] == 4294967295 for x in items))
            self.assertIn(10057, {x['item_id'] for x in items})
            m14 = next(x for x in items if x['item_id'] == 10057)
            self.assertEqual(m14['experience'], 121230)
            self.assertEqual(next(x for x in items if x['item_id'] == 10035)['experience'], 71200)
            encoded = next(x for x in restored.inventory_results(USER_ID) if x[11:16] == bytes.fromhex('0849270000'))
            self.assertEqual(encoded[21:26], bytes.fromhex('088ed90100'))
            self.assertEqual((restored.balance(USER_ID), restored.balance(USER_ID, currency_id=2)), (5000, 20000))
            restored.grant_all(USER_ID)
            self.assertEqual(restored.inventory(USER_ID), items)
            self.assertLess(len(b''.join(restored.inventory_results(USER_ID))), 524000)

    def test_renewal_extends_owned_timed_item_and_preserves_currency_and_permanent_items(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 30000)
            store.purchase(USER_ID, 848, unlock_rank=370)
            store.purchase(USER_ID, 3386)
            expiry = store.inventory(USER_ID)[0]['expires']
            store.renew(USER_ID, 1429, 30)
            restored = MarketplaceStore(root / 'data', root / 'backups')
            self.assertEqual(restored.inventory(USER_ID)[0]['expires'], expiry + 2592000)
            self.assertEqual(restored.balance(USER_ID), 5000)
            before = restored.inventory(USER_ID)
            for item_id, days in [(789, 1), (999999, 1), (1429, 0), (1429, True), (True, 1), (1429, 36501)]:
                with self.assertRaises(ValueError):
                    store.renew(USER_ID, item_id, days)
                self.assertEqual(store.inventory(USER_ID), before)

    def test_expired_renewal_starts_now_and_timestamp_overflow_does_not_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 20000)
            with patch('dw_marketplace.time.time', return_value=1700000000):
                store.purchase(USER_ID, 848, unlock_rank=370)
            with patch('dw_marketplace.time.time', return_value=1800000000):
                self.assertEqual(store.inventory_results(USER_ID), ())
                self.assertEqual(store.renew(USER_ID, 1429, 1)['expires'], 1800086400)
                self.assertEqual(len(store.inventory_results(USER_ID)), 1)
            before = store.inventory(USER_ID)
            with patch('dw_marketplace.time.time', return_value=4294967000), self.assertRaises(ValueError):
                store.renew(USER_ID, 1429, 1)
            self.assertEqual(store.inventory(USER_ID), before)

    def test_premium_purchase_is_independent_persistent_and_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 100)
            self.assertEqual(store.balance(USER_ID, currency_id=2), 0)
            store.add_currency(USER_ID, 1000, currency_id=2)
            # Captured SKU 1: 753 cc, item 100, two days.
            store.purchase(USER_ID, 1, unlock_rank=370)
            store = MarketplaceStore(root / 'data', root / 'backups')
            self.assertEqual(store.balance(USER_ID), 100)
            self.assertEqual(store.balance(USER_ID, currency_id=2), 247)
            self.assertEqual(store.inventory(USER_ID)[0]['item_id'], 100)
            self.assertEqual(store.currency_result(USER_ID, currency_id=2), bytes.fromhex('030208f7000000'))
            self.assertTrue(store.player_assets_result(USER_ID).startswith(bytes.fromhex(
                '0a3bc2d3650c184ae9 1000 0802000000 03010864000000 030208f7000000')))
            before = (root / 'data/e94a180c65d3c23b.json').read_bytes()
            for amount, currency_id in [(True, 2), (-1, 2), (2147483647, 2), (1, 3), (1, True)]:
                with self.assertRaises(ValueError):
                    store.add_currency(USER_ID, amount, currency_id=currency_id)
                self.assertEqual((root / 'data/e94a180c65d3c23b.json').read_bytes(), before)

    def test_rank_gate_cash_rejection_and_timed_purchase_preserve_atomic_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 30000)
            for sku in (848, 1):
                with self.assertRaises(ValueError):
                    store.purchase(USER_ID, sku, unlock_rank=2)
                self.assertEqual(store.balance(USER_ID), 30000)
                self.assertEqual(store.inventory(USER_ID), [])
            before = int(time.time())
            store.purchase(USER_ID, 848, unlock_rank=370)
            self.assertEqual(store.balance(USER_ID), 10000)
            item = MarketplaceStore(root / 'data', root / 'backups').inventory(USER_ID)[0]
            self.assertEqual((item['item_id'], item['quantity']), (1429, 1))
            self.assertTrue(before + 604800 <= item['expires'] <= int(time.time()) + 604800)

    def test_observed_purchase_refreshes_inventory_assets_and_balance_on_the_wire(self):
        purchase = bytes.fromhex('10000801000000083a0d000008010000000801000000010008010000000a00000000000000001000080000000008000000000300080100000000')
        owner = bytes.fromhex('0a3bc2d3650c184ae91000')
        # REA 0xa4b850; permanent item 789, quantity 1, default expiry and limits.
        item = bytes.fromhex('0815030000 0801000000 0800000000 130800000000 08ffffffff 09ffffffffffffff7f 060000 08ffffffff 0300')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 100000)
            auth, _, keys = client_auth()
            tasks = [(8, 1, owner[:9] + b'\0'), (80, 154, purchase),
                     (80, 203, bytes.fromhex('100006204e00')), (80, 230, bytes.fromhex('100000')),
                     (80, 130, bytes.fromhex('080100000000')), (80, 154, purchase),
                     (80, 154, purchase[:-1]), (80, 154, purchase[:8] + bytes(4) + purchase[12:])]
            wire = HELLO + auth + b''.join(request(keys, service=service, task=task, sequence=n+1, parameters=params)
                                         for n, (service, task, params) in enumerate(tasks))
            sock = MemorySocket(wire)
            events = []
            handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                         lambda *_: 'memory', profiles=ProfileStore(root / 'profiles'), marketplace=store)
            self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))
            self.assertEqual(store.balance(USER_ID), 95000)
            replies = []
            for reply in sock.sent[2:]:
                aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(reply[10:26])).decryptor()
                replies.append(aes.update(reply[26:-8]) + aes.finalize())
            self.assertEqual(len(replies), len(tasks))
            self.assertEqual(replies[2][31:31 + len(owner + item)], owner + item)
            expected_assets = owner + bytes.fromhex('0802000000 0301 0818730100 03020800000000 0801000000') + item + bytes.fromhex('0800000000')
            self.assertEqual(replies[3][31:31 + len(expected_assets)], expected_assets)
            self.assertEqual(replies[4][31:38], bytes.fromhex('03010818730100'))
            self.assertEqual([struct.unpack_from('<I', r, 15)[0] for r in replies], [0, 0, 0, 0, 0, 0x1f43, 0x1f43, 0x1f41])

    def test_purchase_debits_catalog_price_and_inventory_survives_reload_and_top_up(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            store.add_currency(USER_ID, 100000)
            # Live capture: SKU 3386 costs 5000 GP and grants permanent item 789.
            store.purchase(USER_ID, 3386)
            self.assertEqual(store.balance(USER_ID), 95000)
            store = MarketplaceStore(root / 'data', root / 'backups')
            self.assertEqual(store.inventory(USER_ID), [{'item_id': 789, 'quantity': 1, 'expires': 4294967295}])
            store.add_currency(USER_ID, 50)
            self.assertEqual(store.inventory(USER_ID)[0]['item_id'], 789)
            before = (root / 'data/e94a180c65d3c23b.json').read_bytes()
            for sku in (0, 3386, True):
                with self.subTest(sku=sku), self.assertRaises(ValueError):
                    store.purchase(USER_ID, sku)
                self.assertEqual((root / 'data/e94a180c65d3c23b.json').read_bytes(), before)
            store.add_currency(USER_ID + 1, 4999)
            with self.assertRaisesRegex(ValueError, '余额不足'):
                store.purchase(USER_ID + 1, 3386)
            self.assertEqual(store.balance(USER_ID + 1), 4999)
            self.assertEqual(store.inventory(USER_ID + 1), [])

    def test_currency_addition_reloads_and_preserves_previous_balance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'data', root / 'backups')
            self.assertEqual(store.balance(USER_ID), 0)
            self.assertEqual(store.add_currency(USER_ID, 100), 100)
            self.assertEqual(store.add_currency(USER_ID, 50), 150)
            self.assertEqual(MarketplaceStore(root / 'data', root / 'backups').balance(USER_ID), 150)
            backups = list((root / 'backups').glob('*.json'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(json.loads(backups[0].read_text())['currency'], 100)
            original = (root / 'data/e94a180c65d3c23b.json').read_bytes()
            for amount in [0, -1, True, 1.5, '100', 2147483647]:
                with self.subTest(amount=amount), self.assertRaises(ValueError):
                    store.add_currency(USER_ID, amount)
                self.assertEqual((root / 'data/e94a180c65d3c23b.json').read_bytes(), original)
            self.assertEqual(store.add_currency(USER_ID, 2147483497), 2147483647)
            self.assertEqual(store.balance(USER_ID + 1), 0)

    def test_observed_tasks_return_one_asset_object_and_one_simple_balance(self):
        # Worked wire example from REA 0xa4a6b0 / 0xa64ad0 / 0xa4bd80 / 0xa4c4a0.
        assets = bytes.fromhex('0a3bc2d3650c184ae9 1000 0802000000 0301 0864000000 03020800000000 0800000000 0800000000')
        balance = bytes.fromhex('0301 0864000000')
        auth, _, keys = client_auth()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store = MarketplaceStore(root / 'marketplace', root / 'backups')
            store.add_currency(USER_ID, 100)
            for task, parameters, expected in [(230, bytes.fromhex('100000'), assets),
                                                (130, bytes.fromhex('080100000000'), balance)]:
                events = []
                lookup = request(keys, service=8, task=1, parameters=bytes.fromhex('0a3bc2d3650c184ae900'))
                sock = MemorySocket(HELLO + auth + lookup + request(keys, service=80, task=task,
                                                                   sequence=2, parameters=parameters))
                handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                             lambda *_: 'memory', profiles=ProfileStore(root / 'profiles'), marketplace=store)
                self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))
                reply = sock.sent[-1]
                self.assertEqual(reply[-8:], hmac.digest(keys[20:40], reply[:-8], 'sha1')[:8])
                aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(reply[10:26])).decryptor()
                clear = aes.update(reply[26:-8]) + aes.finalize()
                # transaction/status/task header occupies 21 cleartext bytes.
                self.assertEqual(clear[21:31], bytes.fromhex('08010000000801000000'))
                self.assertEqual(clear[31:31 + len(expected)], expected)


if __name__ == '__main__':
    unittest.main()
