"""Persistent local player profile for the loopback 3.19 services.

profile319.json (next to this file) holds the player name chosen once in the
launcher. The lobby service keeps the client's PROFILE_MGMT (service 8) data:
task 3 writes the player's public info (u32 version, u32, u32, u32 checksum,
blob = zlib of a 32 KiB player-data buffer, then trailing typed values); task 1
reads it back by user ID at login. Without a stored copy the client runs the
new-player onboarding (character, keyboard, training) on every launch.
"""
import json
import os
import re
import struct
from pathlib import Path
from console_store import SCHEMA, unlock_flags

ROOT = Path(os.environ['CODOL319_SERVER_ROOT'])
PROFILE = ROOT / 'profile319.json'
STORE = ROOT / 'local-profiles319'
UID = 1000001                      # local account (auth ticket, bootstrap metadata tag 2)
DEFAULT_NAME = 'LocalPlayer'
NAME_PATTERN = re.compile(r'[A-Za-z0-9_\-\[\]]{3,15}')


def player_name():
    """Name chosen in the launcher, or the old default if none was saved."""
    try:
        name = json.loads(PROFILE.read_text(encoding='utf-8')).get('name', '')
    except (OSError, ValueError):
        return DEFAULT_NAME
    return name if NAME_PATTERN.fullmatch(name or '') else DEFAULT_NAME


def _atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_bytes(data)
    os.replace(temp, path)


def save_public_info(uid, payload):
    """Store the typed payload of a service-8 task-3 write (everything after the task byte)."""
    if not payload or len(payload) > 65536:
        raise ValueError('Unexpected profile payload size')
    _atomic_write(STORE / ('%d-public.bin' % uid), payload)


def load_public_info(uid):
    try:
        return (STORE / ('%d-public.bin' % uid)).read_bytes()
    except OSError:
        return None


def read_request_uids(body):
    """User IDs in a task-1 read: tagged u64 values (tag 10) after the 3-byte header."""
    uids, o = [], 3
    while o + 9 <= len(body) and body[o] == 0x0a:
        uids.append(struct.unpack_from('<Q', body, o + 1)[0]); o += 9
    return uids


def public_info_reply(task, transaction, uids, with_entity=True):
    """Task reply with one result per stored profile. Results follow the client's
    own write layout, preceded by the user ID (bdProfileInfo entity) when with_entity."""
    results = []
    for uid in uids:
        data = load_public_info(uid)
        if data is not None:
            results.append((b'\x0a' + struct.pack('<Q', uid) if with_entity else b'') + data)
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', len(results)) + b'\x08' + struct.pack('<I', len(results)) + b''.join(results), len(results)


# Secure player data (mp/playersecuredata.def, read by the client with service 8 task 2,
# getter 00512120 with secure=1). Deserializer 007F6330: base read (u64 user id, u32 version),
# u32 compressed flag (1 = zlib), u32 must be 1, u32 CRC32 of data bytes 4..0x7FFF, tagged blob,
# then one tagged value per server-replicated field (flag 0x20) in definition order
# (secure_fields319.json, walk 0076C920): field type 0/1/9 -> Int32 (tag 7), 8 -> Float32 (tag 13).
SECURE_SIZE = 0x8000                 # CRC32 + 0x7FFC data bytes, like the public blob
LEVEL70_XP = 3582550                 # Current loaded mp/rankTable.csv, captured 2026-10-16.
LEVEL70_RANK = 70


def secure_fields():
    return json.loads((ROOT / 'secure_fields319.json').read_text(encoding='utf-8'))['fields']


def profile_settings():
    try:
        return json.loads(PROFILE.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def secure_values():
    settings = profile_settings()
    values = {f['name']: settings.get(f['name'], 0) for f in secure_fields()}
    values['experience'] = settings.get('experience', 0)
    values['rank'] = settings.get('rank', level_for(values['experience']))
    values['prestige'] = settings.get('prestige', 0)
    for k, v in values.items():
        if not isinstance(v, (int, float)) or not -(1 << 31) <= v < (1 << 31):
            raise ValueError('Invalid secure value for ' + k)
    return values


def secure_blob(values):
    import zlib
    data = bytearray(SECURE_SIZE - 4)
    struct.pack_into('<II', data, 0, *SCHEMA['ddl_header'])
    for f in secure_fields():
        v = values[f['name']]
        if f['type'] == 8:
            struct.pack_into('<f', data, f['offset'], float(v))
        else:
            struct.pack_into('<i', data, f['offset'], int(v))
    for key, value in unlock_flags(profile_settings()).items():
        struct.pack_into('<H', data, SCHEMA['unlock_flag_offsets'][int(key)], value)
    return struct.pack('<I', zlib.crc32(bytes(data))) + bytes(data)


def secure_payload():
    import zlib
    values = secure_values()
    blob = secure_blob(values)
    packed = zlib.compress(blob)
    head = b''.join(b'\x08' + struct.pack('<I', v) for v in (0, 1, 1, struct.unpack_from('<I', blob)[0]))
    tail = b''
    for f in secure_fields():
        v = values[f['name']]
        tail += (b'\x0d' + struct.pack('<f', float(v))) if f['type'] == 8 else (b'\x07' + struct.pack('<i', int(v)))
    return head + b'\x13\x08' + struct.pack('<I', len(packed)) + packed + tail


def private_info_reply(task, transaction, uid=UID, with_entity=True):
    payload = secure_payload()
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    result = (b'\x0a' + struct.pack('<Q', uid) if with_entity else b'') + payload
    return head + b'\x08' + struct.pack('<I', 1) + b'\x08' + struct.pack('<I', 1) + result


if __name__ == '__main__':
    body = bytes.fromhex('0803010a41420f000000000000')
    assert read_request_uids(body) == [UID]
    print('name', player_name(), 'stored', load_public_info(UID) is not None)


# Marketplace (service 80). Task numbers from the 3.3.3.3 client: 130 getBalance
# (00A461D0, called by marketplace.getbalance), 154 purchaseSKU (00A467E0), 230 entitlements,
# 232 unlock flags, 142 marketplace config. Currency ids from the 3.19 UI (codo.objects.CurrencyObj):
# 1 GP, 2 CP (cash), 3 clan contribution, 4 clan treasure, 5 BSD, 6 ASD, 7 LSD, 8 hero,
# 9 epic hero, 10 DMZ free ticket, 11 DMZ battle ticket.
UNLIMITED = 999999999
WALLET_LAYOUTS = {
    'A': lambda cid, amount: b'\x08' + struct.pack('<I', cid) + b'\x08' + struct.pack('<I', amount),
    'B': lambda cid, amount: b'\x08' + struct.pack('<I', cid) + b'\x0a' + struct.pack('<Q', amount),
    'C': lambda cid, amount: b'\x08' + struct.pack('<I', cid) + b'\x07' + struct.pack('<i', amount),
    # Traced: wallet result deserialize (3.3.3.3 00A4DBE0): uint8 must be 1, uint8 currency id,
    # uint64 amount, uint32 (unknown, 0). Readers 00A390B0 (tag 3), 00A391C0 (tag 0x0A), 00A38A60 (tag 8).
    'D': lambda cid, amount: b'\x03\x01' + b'\x03' + bytes([cid]) + b'\x0a' + struct.pack('<Q', amount) + b'\x08' + struct.pack('<I', 0),
}


WALLET_LAYOUTS['E'] = lambda cid, amount: b'\x03\x01' + b'\x03' + bytes([cid]) + b'\x0a' + struct.pack('<Q', amount)
WALLET_LAYOUTS['F'] = lambda cid, amount: b'\x03' + bytes([cid]) + b'\x0a' + struct.pack('<Q', amount) + b'\x08' + struct.pack('<I', 0)
# 3.19 (traced 00B8DDF0, the wallet slot class at 0C8E4068): uint8 currency id (tag 3) at +0x10,
# uint32 amount (tag 8) at +0x14. This is the layout the 3.19 client uses.
WALLET_LAYOUTS['G'] = lambda cid, amount: b'' + bytes([cid]) + b'' + struct.pack('<I', amount)
# (layout, result count, first currency id) tried in turn with lsg_handshake.py --wallet-rotate.
WALLET_VARIANTS = [('D', 10, 1), ('D', 1, 2), ('E', 10, 1), ('D', 10, 0), ('F', 10, 1), ('B', 10, 1), ('D', 1, 1)]


# Economy: a persistent wallet instead of unlimited money. Purchases cost the SKU's real price
# (sku-prices319.txt, decoded from the client's catalog by the proxy); matches pay per minute.
ECONOMY = ROOT / 'local-profiles319' / 'economy319.json'
WALLET = ROOT / 'local-profiles319' / 'wallet.json'
SKU_PRICES_FILE = ROOT / 'sku-prices319.txt'
DEFAULT_ECONOMY = {
    'unlimited': False,                     # true = old behaviour (999,999,999 of everything)
    'start': {'1': 2000, '2': 0},           # first-run balance: 1 = GP, 2 = CP
    'earn_per_minute': {'1': 100, '2': 5},  # paid when a match ends (by the match host)
    'earn_min_seconds': 60,                 # matches shorter than this pay nothing
    'xp_per_minute': 700,                   # match XP per minute (1.1.1.13 reference: ~700/min)
}
_sku_prices = None


def economy():
    try:
        cfg = json.loads(ECONOMY.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        ECONOMY.parent.mkdir(parents=True, exist_ok=True)
        ECONOMY.write_text(json.dumps(DEFAULT_ECONOMY, indent=2), encoding='utf-8')
        cfg = {}
    return {**DEFAULT_ECONOMY, **cfg}


def wallet():
    try:
        return {k: int(v) for k, v in json.loads(WALLET.read_text(encoding='utf-8')).items()}
    except (OSError, ValueError):
        w = {k: int(v) for k, v in economy()['start'].items()}
        save_wallet(w)
        return w


def save_wallet(w):
    _atomic_write(WALLET, json.dumps(w).encode('utf-8'))


def balance(cid):
    return UNLIMITED if economy()['unlimited'] else wallet().get(str(cid), 0)


def sku_price(sku):
    """(currency id, price, days) of a shop SKU; days 0 = permanent."""
    global _sku_prices
    if _sku_prices is None:
        _sku_prices = {}
        try:
            for line in SKU_PRICES_FILE.read_text(encoding='utf-8').splitlines():
                f = line.split()
                if len(f) == 4 and f[0].isdigit():
                    _sku_prices[int(f[0])] = (int(f[1]), int(f[2]), int(f[3]))
        except OSError:
            pass
    return _sku_prices.get(sku)


def buy_sku(sku):
    """Charge the SKU's price and own its items. Returns (granted items, message)."""
    if sku in owned_skus():
        return sku_items(sku), 'already owned'
    price = sku_price(sku)
    if price and not economy()['unlimited']:
        cid, cost, _days = price
        w = wallet()
        if w.get(str(cid), 0) < cost:
            return [], 'not enough currency %d (%d < %d)' % (cid, w.get(str(cid), 0), cost)
        w[str(cid)] = w.get(str(cid), 0) - cost
        save_wallet(w)
    return add_purchase(sku), 'bought for %s' % (price,)


def rank_table():
    """Shown level and XP from the verified 3.19 client, not the package's old table."""
    return SCHEMA['levels']


def level_for(xp):
    return max(level for level, low in rank_table() if xp >= low)


def earn(seconds):
    """Pay for time played in a match (currency and XP). Returns what was added."""
    cfg = economy()
    if seconds < cfg['earn_min_seconds']:
        return {}
    before = PROFILE.read_bytes() if PROFILE.exists() else None
    settings = json.loads(before) if before is not None else {}
    total = settings.get('experience', 0) + int(cfg['xp_per_minute'] * seconds / 60)
    settings.update(experience=total, rank=level_for(total))
    w = wallet()
    paid = {k: int(v * seconds / 60) for k, v in cfg['earn_per_minute'].items()}
    for k, v in paid.items():
        w[k] = w.get(k, 0) + v
    _atomic_write(PROFILE, json.dumps(settings).encode('utf-8'))
    try:
        save_wallet(w)
    except OSError:
        if before is None:
            PROFILE.unlink()
        else:
            _atomic_write(PROFILE, before)
        raise
    paid['xp'], paid['level'] = total, settings['rank']
    return paid


def wallet_reply(task, transaction, layout='G', max_results=10, first_id=1):
    """getBalance reply: one result per currency id with the player's balance."""
    enc = WALLET_LAYOUTS[layout]
    results = [enc(cid, balance(cid)) for cid in range(first_id, first_id + max_results)]
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', len(results)) + b'\x08' + struct.pack('<I', len(results)) + b''.join(results)


PURCHASES = ROOT / 'local-profiles319' / 'purchases.jsonl'


def record_purchase(body):
    """Keep every purchase request (raw body) so owned items can be served later."""
    PURCHASES.parent.mkdir(parents=True, exist_ok=True)
    with PURCHASES.open('a', encoding='utf-8') as f:
        f.write(json.dumps({'time': __import__('time').time(), 'body': body.hex()}) + '\n')


# Purchases and inventory (3.19). A purchase is service 93 task 131; its body carries the item id
# as the second uint32 field (10 00 | 08 count | 08 id | ...). Owned ids are kept in
# local-profiles319/owned_items.json, served by login assets (80/230) and inventory (80/203).
# 3.19 00B8D050: optional account owner, id/quantity/XP, blob (<=64),
# expiry, usage limit, uint16, expiry duration, status (uint8 or uint32).
# 00B8CD90 initializes the no-limit sentinels; zero is not the permanent default.
OWNED = ROOT / 'local-profiles319' / 'owned_items.json'


def owned_items():
    try:
        return json.loads(OWNED.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []


def purchase_item_id(body):
    """Item id from a 93/131 purchase body (after the 3-byte service header)."""
    b = body[3:]
    if len(b) >= 12 and b[0:2] == b'\x10\x00' and b[2] == 8 and b[7] == 8:
        return struct.unpack_from('<I', b, 8)[0]
    return None


OWNED_SKUS = ROOT / 'local-profiles319' / 'owned_skus.json'
SKU_ITEMS_FILE = ROOT / 'sku-items319.txt'   # "sku product item ..." dumped by the proxy (0080D540/0080CD80)
_sku_items = None


def sku_items(sku):
    """Item ids the client grants for a shop SKU (its product's item list)."""
    global _sku_items
    if _sku_items is None:
        _sku_items = {}
        try:
            for line in SKU_ITEMS_FILE.read_text(encoding='utf-8').splitlines():
                f = line.split()
                if f and f[0].isdigit():
                    _sku_items[int(f[0])] = [int(x) for x in f[2:]]
        except OSError:
            pass
    return _sku_items.get(sku, [])


def owned_skus():
    try:
        return json.loads(OWNED_SKUS.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        # First run: owned_items.json used to hold the purchased SKU ids themselves.
        return owned_items() if OWNED.exists() else []


def add_purchase(sku):
    """Record a bought SKU without discarding items granted by the local console."""
    skus = owned_skus()
    if sku and sku not in skus:
        skus.append(sku)
    items = list(owned_items())
    for s in skus:
        for it in sku_items(s):
            if it not in items:
                items.append(it)
    OWNED.parent.mkdir(parents=True, exist_ok=True)
    OWNED_SKUS.write_text(json.dumps(skus), encoding='utf-8')
    OWNED.write_text(json.dumps(items), encoding='utf-8')
    return sku_items(sku)


def add_owned(item_id):
    items = owned_items()
    if item_id and item_id not in items:
        items.append(item_id)
        OWNED.parent.mkdir(parents=True, exist_ok=True)
        OWNED.write_text(json.dumps(items), encoding='utf-8')
    return items


def inventory_item(item_id, keyed=False):
    head = (b'\x0a' + struct.pack('<Q', UID) + b'\x10\x00') if keyed else b''
    return (head + b'\x08' + struct.pack('<I', item_id) + b'\x08' + struct.pack('<I', 1)
            + b'\x08' + struct.pack('<I', 0) + b'\x13\x08' + struct.pack('<I', 0)
            + b'\x08' + struct.pack('<I', 0xffffffff) + b'\x09' + struct.pack('<q', 0x7fffffffffffffff)
            + b'\x06' + struct.pack('<H', 0) + b'\x08' + struct.pack('<I', 0xffffffff) + b'\x08' + struct.pack('<I', 0))


def player_assets_reply(task, transaction):
    """80/230 login result (00B87C00 -> 00B8BB90), with inherited account owners."""
    items = owned_items()
    owner = b'\x0a' + struct.pack('<Q', UID) + b'\x10\x00'
    currencies = b''.join(WALLET_LAYOUTS['G'](cid, balance(cid)) for cid in (1, 2))
    assets = (owner + b'\x08' + struct.pack('<I', 2) + currencies
              + b'\x08' + struct.pack('<I', len(items))
              + b''.join(inventory_item(item) for item in items)
              + b'\x08' + struct.pack('<I', 0))  # No entitlements (00B8D6A0).
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', 1) + b'\x08' + struct.pack('<I', 1) + assets


def inventory_reply(task, transaction, keyed=False):
    results = [inventory_item(i, keyed) for i in owned_items()]
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', len(results)) + b'\x08' + struct.pack('<I', len(results)) + b''.join(results)


def all_registry_items():
    """Every item id in the client's item registry (item-registry319.json)."""
    try:
        return [i for i, _ in json.loads((ROOT / 'item-registry319.json').read_text(encoding='utf-8'))['items']]
    except (OSError, ValueError, KeyError):
        return []


def inventory_reply_all(task, transaction, keyed=True, limit=20000):
    """Inventory with every registry item plus purchases (--own-everything)."""
    ids = list(dict.fromkeys(all_registry_items() + owned_items()))[:limit]
    results = [inventory_item(i, keyed) for i in ids]
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', len(results)) + b'\x08' + struct.pack('<I', len(results)) + b''.join(results), len(ids)


APPEARANCE_PREFIXES = ('cha', 'fpa', 'han', 'hea', 'heg', 'fja', 'boo', 'ves', 'eye', 'elp', 'pat', 'bod',
                       'knp', 'bar', 'pet', 'emo', 'spr', 'tat')


def appearance_items():
    """Characters and role-appearance parts (item ids from the client's own id table)."""
    try:
        items = json.loads((ROOT / 'item-registry319.json').read_text(encoding='utf-8'))['items']
    except (OSError, ValueError, KeyError):
        return []
    return [i for i, n in items if n.split('_')[0] in APPEARANCE_PREFIXES]


def inventory_reply_ids(task, transaction, ids, keyed=True):
    ids = list(dict.fromkeys(ids))[:20000]
    results = [inventory_item(i, keyed) for i in ids]
    head = b'\x0a' + struct.pack('<Q', transaction) + b'\x08' + struct.pack('<I', 0) + b'\x03' + bytes([task])
    return head + b'\x08' + struct.pack('<I', len(results)) + b'\x08' + struct.pack('<I', len(results)) + b''.join(results), len(ids)
