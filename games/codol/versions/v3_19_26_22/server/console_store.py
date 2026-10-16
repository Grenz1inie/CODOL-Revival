"""Offline console edits for one 3.19 server directory."""
import json
import os
from pathlib import Path
import time

UID = '00000000000f4241'
DEFINITIONS = Path(__file__).resolve().parents[1] / 'resources/definitions'
SCHEMA = json.loads((DEFINITIONS / 'profile319.json').read_text(encoding='utf-8'))


def read_json(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def integer(value, low, high, label):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f'{label}需为 {low}–{high} 的整数')
    return value


def unlock_flags(settings):
    if not isinstance(settings, dict):
        raise ValueError('玩家档案格式错误')
    flags = settings.get('unlock_flags', {})
    if not isinstance(flags, dict):
        raise ValueError('解锁条件档案格式错误')
    for key, value in flags.items():
        if not isinstance(key, str) or not key.isdecimal() or str(int(key)) != key:
            raise ValueError('解锁条件 ID 格式错误')
        integer(int(key), 0, len(SCHEMA['unlock_flag_offsets']) - 1, '解锁条件 ID')
        integer(value, 0, 65535, '解锁条件值')
    return dict(flags)


class ConsoleStore:
    def __init__(self, runtime):
        self.runtime = Path(runtime)
        self.root = self.runtime / 'server'
        self.data = self.root / 'local-profiles319'
        self.profile = self.root / 'profile319.json'

    def save(self, path, value):
        data = (json.dumps(value, ensure_ascii=False) + '\n').encode('utf-8')
        if path.exists():
            backup = self.runtime / 'backups' / f'{time.time_ns()}-{path.name}'
            backup.parent.mkdir(parents=True, exist_ok=True)
            backup.write_bytes(path.read_bytes())
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + '.tmp')
        try:
            temporary.write_bytes(data)
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def validate_user(self, uid):
        if uid != UID or not self.profile.is_file():
            raise ValueError('需要当前安装的有效账号；请先启动游戏生成档案')

    def economy(self):
        cfg = read_json(self.data / 'economy319.json', {})
        if not isinstance(cfg, dict):
            raise ValueError('经济配置格式错误')
        return cfg

    def wallet(self):
        wallet = read_json(self.data / 'wallet.json', self.economy().get('start', {'1': 2000, '2': 0}))
        if not isinstance(wallet, dict):
            raise ValueError('余额档案格式错误')
        for value in wallet.values():
            integer(value, 0, 0xffffffff, '余额')
        return wallet

    def summary(self):
        settings = read_json(self.profile, {})
        if not isinstance(settings, dict):
            raise ValueError('玩家档案格式错误')
        wallet = self.wallet()
        unlimited = self.economy().get('unlimited', False)
        return {'user_id': UID, 'name': settings.get('name', 'Player'),
                'currency': 999999999 if unlimited else wallet.get('1', 0),
                'premium': 999999999 if unlimited else wallet.get('2', 0),
                'level': settings.get('rank', 1), 'prestige': settings.get('prestige', 0)}

    def set_progression(self, level, prestige):
        integer(level, 1, SCHEMA['max_level'], '等级')
        integer(prestige, 0, SCHEMA['max_prestige'], '转生次数')
        settings = read_json(self.profile, {})
        flags = unlock_flags(settings)
        flags['1'] = prestige * 100 + level
        settings.update(rank=level, prestige=prestige, experience=dict(SCHEMA['levels'])[level],
                        rankVersion=SCHEMA['rank_version'], unlock_flags=flags)
        self.save(self.profile, settings)
        return {'level': level, 'prestige': prestige}

    def unlock_story(self):
        settings = read_json(self.profile, {})
        flags = unlock_flags(settings)
        for key in SCHEMA['story_flags']:
            flags[str(key)] = max(1, flags.get(str(key), 0))
        settings['unlock_flags'] = flags
        self.save(self.profile, settings)
        return {'story_prerequisites_unlocked': len(SCHEMA['story_flags'])}

    def add_currency(self, amount, currency):
        integer(amount, 1, 0xffffffff, '增加数量')
        if self.economy().get('unlimited'):
            raise ValueError('当前档案启用了无限货币模式，无法增加固定余额')
        wallet = self.wallet()
        wallet[currency] = integer(wallet.get(currency, 0) + amount, 0, 0xffffffff, '余额')
        self.save(self.data / 'wallet.json', wallet)
        return {'currency' if currency == '1' else 'premium': wallet[currency]}

    def catalog(self):
        source = read_json(self.root / 'item-registry319.json', {})
        rows = source.get('items') if isinstance(source, dict) else None
        if not isinstance(rows, list) or not rows:
            raise ValueError('当前版本物品目录缺失或为空')
        result = {}
        for row in rows:
            if not isinstance(row, list) or len(row) != 2 or not isinstance(row[1], str):
                raise ValueError('物品目录格式错误')
            result[integer(row[0], 1, 0xffffffff, '物品 ID')] = row[1]
        return result

    def owned(self):
        items = read_json(self.data / 'owned_items.json', [])
        if not isinstance(items, list):
            raise ValueError('库存档案格式错误')
        return list(dict.fromkeys(integer(i, 1, 0xffffffff, '物品 ID') for i in items))

    def inventory(self):
        catalog = self.catalog()
        return {'items': [{'item_id': i, 'name': catalog.get(i, str(i)), 'quantity': 1,
                           'experience': 0, 'expires': 0} for i in self.owned()]}

    def grant_all(self):
        catalog = self.catalog()
        current = self.owned()
        items = list(dict.fromkeys(current + list(catalog)))
        # Freeze the legacy SKU fallback before appending item IDs; later purchases
        # must not treat newly granted item IDs as already purchased SKUs.
        skus = self.data / 'owned_skus.json'
        existing_skus = read_json(skus, current)
        if not isinstance(existing_skus, list):
            raise ValueError('购买记录格式错误')
        for sku in existing_skus:
            integer(sku, 1, 0xffffffff, 'SKU ID')
        if not skus.exists():
            self.save(skus, current)
        self.save(self.data / 'owned_items.json', items)
        return {'items': len(items), 'added': len(items) - len(current)}
