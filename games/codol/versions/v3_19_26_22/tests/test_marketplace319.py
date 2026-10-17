"""Purchases against isolated 3.19 profiles, including console grants."""
import json
from pathlib import Path
import tempfile
import unittest
import struct
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.server.console_store import ConsoleStore
from test_inventory319 import load_profile
from lobby_client319 import connect_lobby


class Marketplace319Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runtime = Path(self.temp.name)
        self.server = self.runtime / 'server'
        self.data = self.server / 'local-profiles319'
        self.data.mkdir(parents=True)
        (self.data / 'wallet.json').write_text('{"1":2000,"2":50,"7":81}')
        (self.data / 'economy319.json').write_text('{"unlimited":false}')
        (self.data / 'owned_items.json').write_text('[]')
        (self.data / 'owned_skus.json').write_text('[]')
        (self.server / 'item-registry319.json').write_text(
            '{"items":[[2200,"m4_mp"],[2252,"m4a1tech_mp"],[99,"other"]]}')
        (self.server / 'sku-items319.txt').write_text(
            '500 10 2200\n501 10 2200\n502 11 2252\n503 12 2200 2252\n504 13 99\n')
        (self.server / 'sku-prices319.txt').write_text(
            '500 1 1200 0\n501 2 20 30\n502 2 25 0\n503 1 1500 0\n504 2 60 0\n')
        (self.server / 'common-ready.json').write_text('{}')
        self.profile = load_profile(self.server)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.data.glob('*.json')}

    def test_console_grants_block_other_skus_without_charging_or_faking_history(self):
        ConsoleStore(self.runtime).grant_all()
        before = self.snapshot()
        for sku in (500, 501, 503):
            with self.subTest(sku=sku):
                with self.assertRaisesRegex(ValueError, 'already owned') as caught:
                    self.profile.buy_sku(sku)
                self.assertEqual(caught.exception.code, 0x1f97)
        reloaded = load_profile(self.server)
        self.assertEqual(reloaded.wallet(), {'1': 2000, '2': 50, '7': 81})
        self.assertEqual(reloaded.owned_items(), [2200, 2252, 99])
        self.assertEqual(reloaded.owned_skus(), [])
        self.assertEqual(self.snapshot(), before)

    def test_new_purchase_and_partly_owned_bundle_keep_catalog_prices_and_survive_reload(self):
        self.assertEqual(self.profile.buy_sku(500)[0], [2200])
        self.assertEqual(self.profile.wallet(), {'1': 800, '2': 50, '7': 81})
        before = self.snapshot()
        for sku in (500, 501):
            with self.subTest(sku=sku), self.assertRaisesRegex(ValueError, 'already owned'):
                self.profile.buy_sku(sku)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.profile.buy_sku(502)[0], [2252])
        reloaded = load_profile(self.server)
        self.assertEqual(reloaded.wallet(), {'1': 800, '2': 25, '7': 81})
        self.assertEqual(reloaded.owned_items(), [2200, 2252])
        self.assertEqual(reloaded.owned_skus(), [500, 502])

        # A bundle with an unowned item still costs its existing full price.
        (self.data / 'owned_items.json').write_text('[99,2200]')
        (self.data / 'owned_skus.json').write_text('[]')
        (self.data / 'wallet.json').write_text('{"1":1500,"2":50,"7":81}')
        self.assertEqual(reloaded.buy_sku(503)[0], [2200, 2252])
        self.assertEqual(reloaded.owned_items(), [99, 2200, 2252])
        self.assertEqual(reloaded.wallet(), {'1': 0, '2': 50, '7': 81})

    def test_insufficient_funds_and_incomplete_catalog_reject_without_writes(self):
        (self.data / 'wallet.json').write_text('{"1":1199,"2":19}')
        before = self.snapshot()
        for sku in (500, 501):
            with self.subTest(sku=sku):
                with self.assertRaisesRegex(ValueError, 'not enough') as caught:
                    self.profile.buy_sku(sku)
                self.assertEqual(caught.exception.code, 0x1f47)
        self.assertEqual(self.snapshot(), before)
        for prices, items in [('500 1 10 0\n', ''), ('', '500 10 2200\n')]:
            (self.server / 'sku-prices319.txt').write_text(prices)
            (self.server / 'sku-items319.txt').write_text(items)
            profile = load_profile(self.server)
            for sku in (500, 999):
                with self.subTest(sku=sku, prices=prices):
                    with self.assertRaisesRegex(ValueError, 'catalog') as caught:
                        profile.buy_sku(sku)
                    self.assertEqual(caught.exception.code, 0x1f43)
            self.assertEqual(self.snapshot(), before)

    def test_lobby_reports_purchase_errors_and_keeps_connection_usable(self):
        (self.data / 'owned_items.json').write_text('[2200]')
        request = connect_lobby(self, self.server)
        def buy(service, task, sku):
            body = bytes([service, 3, task]) + b'\x10\0\x08\x01\0\0\0\x08' + struct.pack('<I', sku)
            reply = request(body)
            self.assertEqual(reply[14:16], bytes([3, task]))
            return struct.unpack_from('<I', reply, 10)[0]
        before = self.snapshot()
        self.assertEqual(buy(80, 154, 500), 0x1f97)
        self.assertEqual(buy(93, 131, 501), 0x1f97)
        self.assertEqual(buy(80, 154, 999), 0x1f43)
        self.assertEqual(buy(93, 131, 504), 0x1f47)
        self.assertEqual(struct.unpack_from('<I', request(b'\x50\x03\x9a'), 10)[0], 0x1f43)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(buy(80, 154, 503), 0)
        self.assertEqual(self.profile.wallet(), {'1': 500, '2': 50, '7': 81})
        self.assertEqual(self.profile.owned_items(), [2200, 2252])
        # Repeated request uses persisted ownership.
        self.assertEqual(buy(80, 154, 503), 0x1f97)
        self.assertEqual(self.profile.wallet()['1'], 500)
        (self.data / 'wallet.json').write_text('{"1":500,"2":60,"7":81}')
        self.assertEqual(buy(93, 131, 504), 0)
        reloaded = load_profile(self.server)
        self.assertEqual(reloaded.wallet(), {'1': 500, '2': 0, '7': 81})
        self.assertEqual(reloaded.owned_items(), [2200, 2252, 99])

    def test_purchase_write_failures_restore_all_three_files(self):
        for missing_history in (False, True):
            for failed_name in ('wallet.json', 'owned_items.json', 'owned_skus.json'):
                with self.subTest(missing_history=missing_history, failed=failed_name):
                    (self.data / 'wallet.json').write_text('{"1":2000,"2":50,"7":81}')
                    (self.data / 'owned_items.json').write_text('[99]')
                    history = self.data / 'owned_skus.json'
                    if missing_history:
                        history.unlink(missing_ok=True)
                    else:
                        history.write_text('[]')
                    before = self.snapshot()
                    replace = self.profile.os.replace
                    def fail_selected(source, target):
                        if Path(target).name == failed_name:
                            raise OSError('simulated disk error')
                        return replace(source, target)
                    with patch.object(self.profile.os, 'replace', side_effect=fail_selected):
                        with self.assertRaisesRegex(ValueError, 'storage') as caught:
                            self.profile.buy_sku(500)
                    self.assertEqual(caught.exception.code, 0x1f45)
                    self.assertEqual(self.snapshot(), before)
                    self.assertEqual(list(self.data.glob('*.tmp')), [])

    def test_success_backs_up_previous_data_and_keeps_free_and_unlimited_modes(self):
        before = self.snapshot()
        self.profile.buy_sku(500)
        backups = {p.name: p.read_bytes() for p in (self.runtime / 'backups').rglob('*.json')}
        for name in ('wallet.json', 'owned_items.json', 'owned_skus.json'):
            self.assertEqual(backups[name], before[name])
        (self.data / 'economy319.json').write_text('{"unlimited":true}')
        before_wallet = (self.data / 'wallet.json').read_bytes()
        self.profile.buy_sku(502)
        self.assertEqual((self.data / 'wallet.json').read_bytes(), before_wallet)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'already owned'):
            self.profile.buy_sku(501)
        self.assertEqual(self.snapshot(), before)
        (self.data / 'economy319.json').write_text('{"unlimited":false}')
        (self.data / 'owned_items.json').write_text('[]')
        (self.data / 'owned_skus.json').write_text('[]')
        (self.server / 'sku-prices319.txt').write_text('502 2 0 0\n')
        profile = load_profile(self.server)
        self.assertEqual(profile.buy_sku(502)[0], [2252])
        self.assertEqual(profile.wallet(), {'1': 800, '2': 50, '7': 81})


if __name__ == '__main__':
    unittest.main()
