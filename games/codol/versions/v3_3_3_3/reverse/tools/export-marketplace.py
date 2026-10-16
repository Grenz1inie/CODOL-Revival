"""Decode the read-only catalogue capture using REA 0x5840a0/0x7070b0/0x706f10."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[6]
source = ROOT / 'research/evidence/live-marketplace.json'
capture = json.loads(source.read_text(encoding='utf-8'))
if capture['exe_sha256'] != 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b':
    raise ValueError('Unsupported client')
catalogue = capture['catalogue']
requirements_raw = bytes.fromhex(catalogue['requirements']['hex'])
requirements = {struct.unpack_from('<H', requirements_raw, index * 8)[0]: name
                for index, name in enumerate(catalogue['requirements']['names'])}
products = {}
raw = bytes.fromhex(catalogue['products']['hex'])
for index in range(catalogue['products']['count']):
    product_id, requirement, threshold = struct.unpack_from('<HHH', raw, index * 24)
    entries = bytes.fromhex(catalogue['products']['items'][index])
    products[product_id] = {
        'requirement': requirements[requirement], 'threshold': threshold,
        'items': [list(struct.unpack_from('<HB', entries, offset)) for offset in range(0, len(entries), 4)],
    }
raw = bytes.fromhex(catalogue['skus']['hex'])
skus = {}
for index in range(1, catalogue['skus']['count']):
    address = catalogue['skus']['address'] + index * 24
    values = []
    for field in range(7):
        value = (struct.unpack_from('<H', raw, index * 24 + field * 2)[0]
                 ^ (catalogue['sku_keys'][field] & 65535) ^ ((address + field * 2) & 65535))
        values.append(((value << 4) | (value >> 12)) & 65535)
    sku, flags, product, cc, cp, duration, _ = values
    if not flags & 1 or product not in products:
        continue
    skus[str(sku)] = {**products[product], 'product_id': product, 'price': cp, 'cash_price': cc,
                      'duration_days': duration, 'ignore_requirement': bool(flags & 2)}
weapon_source = ROOT / 'research/evidence/live-weapon-progression.json'
weapon_capture = json.loads(weapon_source.read_text(encoding='utf-8'))
if weapon_capture['exe_sha256'] != capture['exe_sha256']:
    raise ValueError('Weapon table belongs to another client')
raw = bytes.fromhex(catalogue['items']['hex'])
weapon_types = {}
for index in range(1, catalogue['items']['count']):
    address = catalogue['items']['address'] + index * 40
    value = struct.unpack_from('<H', raw, index * 40)[0] ^ (address & 65535) ^ (catalogue['item_key'] & 65535)
    item_id = ((value << 4) | (value >> 12)) & 65535
    weapon_types[item_id] = raw[index * 40 + 6]
items = {}
for row in capture['tables']['mp/coMarketplaceItems.csv']:
    item = {'name': row[1], 'kind': row[2], 'category': row[3]}
    if row[2] == 'wea':
        # REA 0x6b7190: subtype <6 chooses primary table, result rank +1 is UI level.
        table = 'mp/coWeaponPrimaryRankTable.csv' if weapon_types[int(row[0])] < 6 else 'mp/coWeaponSecondaryRankTable.csv'
        last = weapon_capture['tables'][table][-1]
        item.update(max_experience=int(last[1]), max_level=int(last[0]) + 1)
    items[row[0]] = item
output = ROOT / 'games/codol/versions/v3_3_3_3/resources/definitions/marketplace-catalog.json'
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps({'exe_sha256': capture['exe_sha256'],
                              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                              'weapon_source_sha256': hashlib.sha256(weapon_source.read_bytes()).hexdigest(),
                              'items': items,
                              'skus': skus}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(f'{output}: {len(skus)} enabled SKUs')
