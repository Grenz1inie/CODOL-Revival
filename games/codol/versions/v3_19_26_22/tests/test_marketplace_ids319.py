"""Legacy console IDs must reach the IDs used by the client's shop products."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

from games.codol.versions.v3_19_26_22.server.console_store import ConsoleStore
from test_inventory319 import load_profile


# old grant ID, shop item ID, native registry slot, SKU, product, name.
# From this version's item-ids319.txt and sku-items319.txt, not name matching.
WEAPONS = (
    (2201, 10002, 796, 129, 65, 'famas_mp'),
    (2202, 10003, 797, 131, 66, 'scar_mp'),
    (2205, 10006, 800, 137, 69, 'm16_mp'),
    (2208, 10009, 803, 143, 72, 'ak47_mp'),
    (2212, 10013, 807, 151, 76, 'p90_mp'),
    (2220, 10021, 815, 167, 84, 'cheytac_mp'),
    (2229, 10030, 824, 185, 93, 'aa12_mp'),
    (2237, 10038, 832, 201, 101, 'deserteagle_mp'),
)


class MarketplaceIdFixture(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.runtime = Path(temporary.name)
        self.root = self.runtime / 'server'
        self.data = self.root / 'local-profiles319'
        self.data.mkdir(parents=True)
        (self.data / 'wallet.json').write_text('{"1":10000,"2":5000}')
        (self.data / 'economy319.json').write_text('{"unlimited":false}')
        (self.data / 'owned_skus.json').write_text('[]')
        (self.data / 'owned_items.json').write_text(json.dumps([w[0] for w in WEAPONS]))
        (self.root / 'item-registry319.json').write_text(json.dumps(
            {'items': [[w[0], w[5]] for w in WEAPONS] + [[99, 'not_for_sale']]}))
        (self.root / 'item-ids319.txt').write_text('# id slot name\n' + ''.join(
            f'{item} {slot} {name}\n' for old, shop, slot, _, _, name in WEAPONS for item in (old, shop)))
        (self.root / 'sku-items319.txt').write_text(''.join(
            f'{sku} {product} {shop}\n' for _, shop, _, sku, product, _ in WEAPONS)
            + '13794 6977 10009\n500 102 10009 10013\n')
        (self.root / 'sku-prices319.txt').write_text('143 1 3400 0\n13794 2 1780 0\n500 1 5000 0\n')
        self.profile = load_profile(self.root)
        self.store = ConsoleStore(self.runtime)


class MarketplaceIds319Tests(MarketplaceIdFixture):
    def test_existing_grants_reach_shop_ids_without_rewriting_saves(self):
        old = [w[0] for w in WEAPONS]
        expected = [w[1] for w in WEAPONS] + [99, 65000]
        owned = self.data / 'owned_items.json'
        owned.write_text(json.dumps(old + [10009, 99, 65000]))
        before = owned.read_bytes()
        self.assertEqual(self.profile.owned_items(), expected)
        self.assertEqual([i['item_id'] for i in self.store.inventory()['items']], expected)
        self.assertEqual(self.store.inventory()['items'][3]['name'], 'ak47_mp')
        for reply, keyed in ((self.profile.inventory_reply(203, 1), False),
                             (self.profile.inventory_reply(165, 1, keyed=True), True)):
            stride, offset = (59, 38) if keyed else (48, 27)
            self.assertEqual(struct.unpack_from('<I', reply, 17)[0], len(expected))
            self.assertEqual([struct.unpack_from('<I', reply, offset + i*stride)[0]
                              for i in range(len(expected))], expected)
        reply = self.profile.player_assets_reply(230, 1)[26:]
        raw = zlib.decompress(reply[16:]) if reply[0] == 0x16 else reply
        self.assertEqual([struct.unpack_from('<I', raw, 36 + i*48)[0]
                          for i in range(len(expected))], expected)
        self.assertEqual(owned.read_bytes(), before)
        self.assertEqual(self.profile.owned_skus(), [])

    def test_unlock_uses_registry_identity_keeps_unlisted_items_and_legacy_skus(self):
        # An unlisted ID with the same name must not become the same item.
        catalog = self.root / 'item-registry319.json'
        rows = json.loads(catalog.read_text())
        rows['items'].append([999, 'ak47_mp'])
        catalog.write_text(json.dumps(rows))
        owned = self.data / 'owned_items.json'
        owned.write_text('[2208,10009,65000]')
        before = owned.read_bytes()
        history = self.data / 'owned_skus.json'
        history.unlink()
        self.assertEqual(self.profile.owned_skus(), [2208, 10009, 65000])
        self.assertEqual(self.store.grant_all(), {'items': 11, 'added': 9})
        self.assertEqual(self.store.grant_all(), {'items': 11, 'added': 0})
        self.assertEqual(json.loads(history.read_text()), [2208, 10009, 65000])
        ids = json.loads(owned.read_text())
        self.assertEqual(ids[:2], [10009, 65000])
        self.assertIn(999, ids)
        self.assertIn(99, ids)
        self.assertNotIn(2208, ids)
        self.assertIn(before, [p.read_bytes() for p in (self.runtime / 'backups').glob('*owned_items.json')])
        self.assertEqual(self.profile.all_registry_items(), [w[1] for w in WEAPONS] + [99, 999])

    def test_legacy_weapon_blocks_both_currencies_and_complete_bundle(self):
        before = {p.name: p.read_bytes() for p in self.data.glob('*.json')}
        for sku in (143, 13794, 500):
            with self.subTest(sku=sku):
                with self.assertRaisesRegex(ValueError, 'already owned') as error:
                    self.profile.buy_sku(sku)
                self.assertEqual(error.exception.code, 0x1f97)
        self.assertEqual({p.name: p.read_bytes() for p in self.data.glob('*.json')}, before)
        (self.data / 'owned_items.json').write_text('[2208]')
        self.assertEqual(self.profile.buy_sku(500)[0], [10009, 10013])
        self.assertEqual(self.profile.wallet()['1'], 5000)
        self.assertEqual(load_profile(self.root).owned_items(), [10009, 10013])

    def test_conflicting_shop_ids_do_not_silently_choose_or_rewrite_inventory(self):
        with (self.root / 'sku-items319.txt').open('a') as stream:
            stream.write('999 999 2208\n')
        before = (self.data / 'owned_items.json').read_bytes()
        with self.assertRaisesRegex(ValueError, '商城.*ID'):
            self.store.grant_all()
        self.assertEqual((self.data / 'owned_items.json').read_bytes(), before)


class NativeMarketplaceIds319Tests(MarketplaceIdFixture):
    @classmethod
    def setUpClass(cls):
        try:
            from client_marketplace319 import MarketplaceReader319
            cls.reader = MarketplaceReader319(WEAPONS)
        except (FileNotFoundError, ImportError) as error:
            raise unittest.SkipTest('Captured 3.19 reader unavailable: ' + str(error))

    def test_native_shop_recognizes_all_eight_existing_weapons_as_permanent(self):
        self.reader.publish(self.profile.player_assets_reply(230, 1)[26:])
        for _, shop, _, _, product, _ in WEAPONS:
            with self.subTest(item=shop):
                self.assertTrue(self.reader.permanent(product))
                self.assertEqual(self.reader.product_flags(shop), (True, True))
        # A partially owned bundle must remain purchasable.
        (self.data / 'owned_items.json').write_text('[2208]')
        self.reader.publish(self.profile.player_assets_reply(230, 2)[26:])
        self.assertTrue(self.reader.permanent(72))
        self.assertFalse(self.reader.permanent(76))
        self.assertFalse(self.reader.permanent(102))


if __name__ == '__main__':
    unittest.main()
