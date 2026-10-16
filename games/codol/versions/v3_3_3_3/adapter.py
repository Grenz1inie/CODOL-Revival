"""3.3.3.3 console operations and process context; no cross-version imports."""
import json
import os
from pathlib import Path
import re

from .server.dw_profiles import validate_profile
from .server.dw_marketplace import MarketplaceStore
from .server.dw_progression import PrivateProfileStore

VERSION_ROOT = Path(__file__).resolve().parent
CAPABILITIES = {
    'progression': {'available': True, 'reason': '此版本上限为 3 转生、70 级；同时更新商城等级解锁值。', 'max_level': 70, 'max_prestige': 3},
    'currency': {'available': True, 'reason': '游戏币与点券独立保存；退出游戏后修改，重登生效。'},
    'inventory': {'available': True, 'reason': '发放 6772 种物品（含配件与皮肤），武器使用满级经验；永久保存，已有数量不叠加。'},
    'story': {'available': True, 'reason': '解除剧情前置条件；地图可玩性仍待验证。'},
    'launch': {'available': True, 'reason': ''},
    'skip_tutorial': {'available': True, 'reason': ''},
}


class Adapter:
    capabilities = CAPABILITIES

    def __init__(self, root, selection, runtime):
        self.root, self.selection, self.runtime = Path(root), selection, Path(runtime)
        self.marketplace = MarketplaceStore(self.runtime / 'data/marketplace', self.runtime / 'backups/marketplace')
        self.progression = PrivateProfileStore(self.runtime / 'data/private-profiles', self.runtime / 'backups/private-profiles')

    def environment(self):
        return {**os.environ, 'CODOL_GAME_ROOT': self.selection['path'],
                'CODOL_RUNTIME': str(self.runtime), 'CODOL_REPO_ROOT': str(self.root),
                'CODOL_VERSION_ROOT': str(VERSION_ROOT),
                'PYTHONPATH': str(self.root)}

    def settings(self):
        path = self.runtime / 'data/controller.json'
        return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {'skip_tutorial': True}

    def set_settings(self, body):
        if set(body) != {'skip_tutorial'} or type(body['skip_tutorial']) is not bool:
            raise ValueError('skip_tutorial 必须是布尔值')
        path = self.runtime / 'data/controller.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(body), encoding='utf-8')
        temporary.replace(path)
        return self.settings()

    def profiles(self):
        result = []
        for path in sorted((self.runtime / 'data/public-profiles').glob('*.bin')):
            if re.fullmatch('[0-9a-f]{16}', path.stem):
                validate_profile(path.read_bytes())
                uid = int(path.stem, 16)
                result.append({'user_id': path.stem, 'currency': self.marketplace.balance(uid),
                               'premium': self.marketplace.balance(uid, currency_id=2), **self.progression.summary(uid)})
        return result

    def validate_user(self, uid):
        if not isinstance(uid, str) or not re.fullmatch('[0-9a-f]{16}', uid):
            raise ValueError('需要有效的账号和操作参数')
        validate_profile((self.runtime / 'data/public-profiles' / (uid + '.bin')).read_bytes())
        return int(uid, 16)

    def inventory(self, uid):
        user = self.validate_user(uid)
        catalog = json.loads((VERSION_ROOT / 'resources/definitions/marketplace-catalog.json').read_text(encoding='utf-8'))['items']
        return {'items': [{**item, 'name': catalog.get(str(item['item_id']), {}).get('name', str(item['item_id']))}
                          for item in self.marketplace.inventory(user)]}

    def mutate(self, action, body):
        fields = {'currency': {'user_id', 'amount'}, 'premium': {'user_id', 'amount'},
                  'progression': {'user_id', 'level', 'prestige'}, 'renew': {'user_id', 'item_id', 'days'},
                  'unlock': {'user_id'}, 'story': {'user_id'}}
        if action not in fields or set(body) != fields[action]:
            raise ValueError('需要有效的账号和操作参数')
        uid = self.validate_user(body['user_id'])
        if action in ('currency', 'premium'):
            currency = 2 if action == 'premium' else 1
            return {self.marketplace.currency_key(currency): self.marketplace.add_currency(uid, body['amount'], currency_id=currency)}
        if action == 'renew': return self.marketplace.renew(uid, body['item_id'], body['days'])
        if action == 'unlock': return self.marketplace.grant_all(uid)
        if action == 'story': return self.progression.unlock_story(uid)
        return self.progression.set_progression(uid, body['level'], body['prestige'])
