"""Local currency state; CODOL wire structures are documented in wiki/08."""
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import threading
import time


class PurchaseError(ValueError):
    def __init__(self, message, code=0x1f43):
        super().__init__(message)
        self.code = code


class MarketplaceStore:
    def __init__(self, directory, backups):
        self.directory = directory
        self.backups = backups
        self.lock = threading.Lock()

    def balance(self, user_id, *, currency_id=1):
        return self._read(user_id)[self.currency_key(currency_id)]

    @staticmethod
    def currency_key(currency_id):
        if type(currency_id) is not int or currency_id not in (1, 2):
            raise ValueError('货币编号必须为 1（游戏币）或 2（点券）')
        return 'currency' if currency_id == 1 else 'premium'

    def _read(self, user_id):
        path = self.directory / f'{user_id:016x}.json'
        if not path.exists():
            return {'currency': 0, 'premium': 0, 'inventory': []}
        record = json.loads(path.read_text(encoding='utf-8'))
        amount = record.get('currency') if isinstance(record, dict) else None
        if type(amount) is not int or not 0 <= amount <= 2147483647:
            raise ValueError('无效的游戏币数据')
        record.setdefault('inventory', [])
        record.setdefault('premium', 0)
        if type(record['premium']) is not int or not 0 <= record['premium'] <= 2147483647:
            raise ValueError('无效的点券数据')
        return record

    def inventory(self, user_id):
        return self._read(user_id)['inventory']

    def _save(self, user_id, record):
        path = self.directory / f'{user_id:016x}.json'
        if path.exists():
            self.backups.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
            (self.backups / f'{stamp}-{user_id:016x}.json').write_bytes(path.read_bytes())
        self.directory.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(record) + '\n', encoding='utf-8')
        temporary.replace(path)

    def add_currency(self, user_id, amount, *, currency_id=1):
        key = self.currency_key(currency_id)
        if type(amount) is not int or not 1 <= amount <= 2147483647:
            raise ValueError('增加数量必须是 1–2147483647 的整数')
        with self.lock:
            record = self._read(user_id)
            balance = record[key] + amount
            if balance > 2147483647:
                raise ValueError('余额总额不能超过 2147483647')
            record[key] = balance
            self._save(user_id, record)
            return balance

    def purchase(self, user_id, sku, *, unlock_rank=0):
        catalogue = json.loads((Path(__file__).resolve().parents[1] / 'data/marketplace-catalog.json').read_text(encoding='utf-8'))['skus']
        product = catalogue.get(str(sku)) if type(sku) is int else None
        if not product or not product['items']:
            raise PurchaseError('商品不存在', 0x1f41)
        currency_id = 2 if product['cash_price'] else 1
        key = self.currency_key(currency_id)
        price = product['cash_price'] or product['price']
        if not product['ignore_requirement'] and product['requirement']:
            if product['requirement'] != 'uf_prestige_rank' or unlock_rank < product['threshold']:
                raise PurchaseError('未满足商品解锁条件')
        with self.lock:
            record = self._read(user_id)
            if record[key] < price:
                raise PurchaseError('余额不足', 0x1f47)
            now = int(time.time())
            item_ids = {item_id for item_id, _ in product['items']}
            if any(item['item_id'] in item_ids and item['expires'] > now for item in record['inventory']):
                raise PurchaseError('物品已拥有，未重复扣款；限时物品可在控制器续期')
            expires = now + product['duration_days'] * 86400 if product['duration_days'] else 0xffffffff
            record['inventory'] = [item for item in record['inventory'] if item['item_id'] not in item_ids]
            record['inventory'] += [{'item_id': item_id, 'quantity': quantity, 'expires': expires}
                                    for item_id, quantity in product['items']]
            record[key] -= price
            self._save(user_id, record)
            return {'sku': sku, 'cost': price, 'currency_id': currency_id,
                    'currency': record['currency'], 'premium': record['premium'], 'items': product['items']}

    def currency_result(self, user_id, *, currency_id=1):
        # Currency ID 1 (cp), typed uint8 then typed uint32: 0xa4c4a0.
        balance = self.balance(user_id, currency_id=currency_id)
        return bytes((3, currency_id, 8)) + struct.pack('<I', balance)

    def renew(self, user_id, item_id, days):
        if type(item_id) is not int or type(days) is not int or not 1 <= days <= 36500:
            raise ValueError('需要物品编号和 1–36500 的整数天数')
        with self.lock:
            record = self._read(user_id)
            item = next((item for item in record['inventory'] if item['item_id'] == item_id), None)
            if item is None:
                raise ValueError('账号未拥有此物品')
            if item['expires'] == 0xffffffff:
                raise ValueError('永久物品无需续期')
            expires = max(item['expires'], int(time.time())) + days * 86400
            if expires >= 0xffffffff:
                raise ValueError('续期日期超出客户端时间范围')
            item['expires'] = expires
            self._save(user_id, record)
            return dict(item)

    def grant_all(self, user_id):
        catalogue = json.loads((Path(__file__).resolve().parents[1] / 'data/marketplace-catalog.json').read_text(encoding='utf-8'))['items']
        with self.lock:
            record = self._read(user_id)
            items = {item['item_id']: item for item in record['inventory']}
            for identifier, definition in catalogue.items():
                item_id = int(identifier)
                item = items.setdefault(item_id, {'item_id': item_id, 'quantity': 1})
                item['expires'] = 0xffffffff
                if 'max_experience' in definition:
                    item['experience'] = definition['max_experience']
            record['inventory'] = list(items.values())
            self._save(user_id, record)
            return {'granted': len(catalogue), 'inventory_count': len(items)}

    def inventory_results(self, user_id, *, inherited_owner=False):
        # 0xa4b850: item ID, quantity, experience, blob, expiry, usage limit,
        # collision ID, modification time, custom-source byte. Defaults: 0xa4b4e0.
        owner = b'' if inherited_owner else b'\x0a' + struct.pack('<Q', user_id) + b'\x10\0'
        results = []
        for item in self.inventory(user_id):
            if item['expires'] <= int(time.time()):
                continue
            value = owner + b''.join(b'\x08' + struct.pack('<I', n) for n in (item['item_id'], item['quantity'], item.get('experience', 0)))
            value += b'\x13\x08' + bytes(4) + b'\x08' + struct.pack('<I', item['expires'])
            value += bytes.fromhex('09ffffffffffffff7f 060000 08ffffffff 0300')
            results.append(value)
        return tuple(results)

    def player_assets_result(self, user_id):
        # 0xa4a6b0 reads owner, balances, inventory, entitlements in that order.
        # Child objects inherit owner, so do not repeat the account ID per balance.
        owner = b'\x0a' + struct.pack('<Q', user_id) + b'\x10\0'
        items = self.inventory_results(user_id, inherited_owner=True)
        return (owner + b'\x08\x02\0\0\0' + self.currency_result(user_id)
                + self.currency_result(user_id, currency_id=2)
                + b'\x08' + struct.pack('<I', len(items)) + b''.join(items) + b'\x08' + bytes(4))
