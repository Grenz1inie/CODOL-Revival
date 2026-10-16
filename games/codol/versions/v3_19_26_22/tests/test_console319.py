import json
import os
from pathlib import Path
import subprocess
import sys
import struct
import zlib
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.adapter import Adapter


UID = '00000000000f4241'


class Console319Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root / 'instance'
        self.server = self.runtime / 'server'
        self.data = self.server / 'local-profiles319'
        self.data.mkdir(parents=True)
        self.profile = self.server / 'profile319.json'
        self.profile.write_text('{"name":"Tester","rank":4,"experience":5833,"other":17}')
        (self.server / 'rankTable319.csv').write_text('0,pvt1,0,500,a,a,a,500,,,,,,1\n3,pvt4,5000,1200,a,a,a,1700,,,,,,4\n69,cmd,2434700,0,a,a,a,0,,,,,,70\n')
        self.wallet = self.data / 'wallet.json'
        self.wallet.write_text('{"1":2000,"2":9,"7":81}')
        self.adapter = Adapter(self.root, {'path': str(self.root)}, self.runtime)

    def test_currency_roundtrip_backups_and_instance_isolation(self):
        before = self.wallet.read_bytes()
        self.assertEqual(self.adapter.profiles()[0],
                         {'user_id': UID, 'name': 'Tester', 'currency': 2000, 'premium': 9,
                          'level': 4, 'prestige': 0})
        self.assertEqual(self.adapter.mutate('currency', {'user_id': UID, 'amount': 100}), {'currency': 2100})
        self.adapter.mutate('premium', {'user_id': UID, 'amount': 50})
        reloaded = Adapter(self.root, {'path': str(self.root)}, self.runtime)
        self.assertEqual(reloaded.profiles()[0]['premium'], 59)
        self.assertEqual(json.loads(self.wallet.read_text())['7'], 81)
        self.assertIn(before, [p.read_bytes() for p in (self.runtime / 'backups').rglob('*.json')])
        second = Adapter(self.root, {'path': str(self.root)}, self.root / 'second')
        self.assertEqual(second.profiles(), [])
        self.assertFalse((self.root / 'second').exists())

    def test_currency_rejects_bad_inputs_corruption_overflow_and_failed_replace(self):
        before = self.wallet.read_bytes()
        for body in [dict(user_id=UID, amount=x) for x in (0, -1, True, 1.5, '1', 1 << 32)] + [
                {'user_id': '../wallet', 'amount': 1}, {'user_id': '0000000000000001', 'amount': 1},
                {'user_id': UID, 'amount': 1, 'extra': 1}]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.adapter.mutate('currency', body)
        self.assertEqual(self.wallet.read_bytes(), before)
        with self.assertRaises(ValueError):
            self.adapter.mutate('currency', {'user_id': UID, 'amount': 0xffffffff})
        with patch('os.replace', side_effect=OSError('disk full')), self.assertRaises(OSError):
            self.adapter.mutate('currency', {'user_id': UID, 'amount': 1})
        self.assertEqual(self.wallet.read_bytes(), before)
        self.wallet.write_text('{broken')
        with self.assertRaises(ValueError): self.adapter.profiles()
        with self.assertRaises(ValueError): self.adapter.mutate('premium', {'user_id': UID, 'amount': 10})
        self.assertEqual(self.wallet.read_text(), '{broken')

    def test_missing_wallet_uses_defaults_without_writes_and_unlimited_is_explicit(self):
        self.wallet.unlink()
        self.assertEqual(self.adapter.profiles()[0]['currency'], 2000)
        self.assertFalse(self.wallet.exists())
        self.adapter.mutate('premium', {'user_id': UID, 'amount': 7})
        self.assertEqual(json.loads(self.wallet.read_text()), {'1': 2000, '2': 7})
        (self.data / 'economy319.json').write_text('{"unlimited":true}')
        self.assertEqual(self.adapter.profiles()[0]['currency'], 999999999)
        with self.assertRaisesRegex(ValueError, '无限'):
            self.adapter.mutate('currency', {'user_id': UID, 'amount': 1})

    def test_grant_complete_registry_preserves_owned_and_survives_purchase(self):
        (self.server / 'item-registry319.json').write_text('{"items":[[11,"weapon"],[12,"appearance"],[13,"not_for_sale"]]}')
        owned = self.data / 'owned_items.json'
        owned.write_text('[11,99]')
        self.assertEqual(self.adapter.mutate('unlock', {'user_id': UID}), {'items': 4, 'added': 2})
        self.assertEqual(self.adapter.mutate('unlock', {'user_id': UID}), {'items': 4, 'added': 0})
        self.assertEqual([i['item_id'] for i in self.adapter.inventory(UID)['items']], [11, 99, 12, 13])
        (self.server / 'sku-items319.txt').write_text('500 501 14\n')
        result = subprocess.run([sys.executable, '-B', '-c',
            'from local_profile319 import add_purchase; add_purchase(500)'],
            cwd=Path(__file__).resolve().parents[1] / 'server',
            env={**os.environ, 'CODOL319_SERVER_ROOT': str(self.server)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(owned.read_text()), [11, 99, 12, 13, 14])
        self.assertEqual(json.loads((self.data / 'owned_skus.json').read_text()), [11, 99, 500])

    def test_grant_rejects_bad_catalog_or_inventory_without_partial_write(self):
        owned = self.data / 'owned_items.json'
        owned.write_text('[99]')
        catalog = self.server / 'item-registry319.json'
        for value in ({'items': []}, {'items': [[11, 'ok'], [False, 'invalid']]}, {'items': [[-1, 'bad']]}):
            catalog.write_text(json.dumps(value))
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.adapter.mutate('unlock', {'user_id': UID})
            self.assertEqual(owned.read_text(), '[99]')
        catalog.write_text('{"items":[[11,"ok"]]}')
        owned.write_text('{broken')
        with self.assertRaises(ValueError): self.adapter.mutate('unlock', {'user_id': UID})
        self.assertEqual(owned.read_text(), '{broken')

    def test_progression_and_story_preserve_fields_and_reach_secure_payload_after_reload(self):
        profile = json.loads(self.profile.read_text())
        profile.update(kills=41, unlock_flags={'159': 7, '140': 2})
        self.profile.write_text(json.dumps(profile))
        before = self.profile.read_bytes()
        self.assertEqual(self.adapter.mutate('progression', {'user_id': UID, 'level': 70, 'prestige': 4}),
                         {'level': 70, 'prestige': 4})
        self.assertEqual(self.adapter.mutate('story', {'user_id': UID}), {'story_prerequisites_unlocked': 10})
        saved = json.loads(self.profile.read_text())
        self.assertEqual((saved['experience'], saved['rankVersion'], saved['kills'], saved['other']),
                         (3582550, 4, 41, 17))
        self.assertEqual(saved['unlock_flags']['1'], 470)
        self.assertEqual(saved['unlock_flags']['159'], 7)
        self.assertEqual(saved['unlock_flags']['140'], 2)
        self.assertIn(before, [p.read_bytes() for p in (self.runtime / 'backups').rglob('*.json')])
        # Use the shipped runtime serializer, in a new process with the selected instance.
        definitions = Path(__file__).resolve().parents[1] / 'resources/definitions'
        (self.server / 'secure_fields319.json').write_bytes((definitions / 'secure_fields319.json').read_bytes())
        result = subprocess.run([sys.executable, '-B', '-c',
            'from local_profile319 import secure_payload; print(secure_payload().hex())'],
            cwd=Path(__file__).resolve().parents[1] / 'server',
            env={**os.environ, 'CODOL319_SERVER_ROOT': str(self.server)}, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        wire = bytes.fromhex(result.stdout.strip())
        size = struct.unpack_from('<I', wire, 22)[0]
        raw = zlib.decompress(wire[26:26 + size])
        self.assertEqual(len(raw), 32768)
        self.assertEqual(struct.unpack_from('<II', raw, 4), (19, 2739108020))
        self.assertEqual(struct.unpack_from('<I', raw)[0], zlib.crc32(raw[4:]))
        self.assertEqual(struct.unpack_from('<iii', raw, 4883), (4, 70, 4))
        self.assertEqual(struct.unpack_from('<H', raw, 8297)[0], 470)
        self.assertEqual([struct.unpack_from('<H', raw, i)[0] for i in range(8595,8615,2)], [1]*9+[7])
        fields = json.loads((definitions / 'secure_fields319.json').read_text())['fields']
        tail = b''.join(bytes([13 if f['type']==8 else 7]) + raw[f['offset']+4:f['offset']+8] for f in fields)
        self.assertEqual(wire[26 + size:], tail)

    def test_progression_rejects_invalid_values_and_story_keeps_corrupt_data(self):
        before = self.profile.read_bytes()
        for level, prestige in ((0, 0), (71, 0), (True, 0), (1, -1), (70, 5), (70, True), ('70', 4)):
            with self.subTest(level=level, prestige=prestige), self.assertRaises(ValueError):
                self.adapter.mutate('progression', {'user_id': UID, 'level': level, 'prestige': prestige})
            self.assertEqual(self.profile.read_bytes(), before)
        self.profile.write_text('{broken')
        with self.assertRaises(ValueError): self.adapter.mutate('story', {'user_id': UID})
        self.assertEqual(self.profile.read_text(), '{broken')
