"""3.19.26.22 integration with instance-local runtime and console data."""
import os
from pathlib import Path
from .client.settings import read_options, save_options
from .server.console_store import ConsoleStore, SCHEMA

VERSION_ROOT = Path(__file__).resolve().parent


class Adapter:
    command_timeout = 600  # First copy plus the original client's login delay.
    capabilities = {name: {'available': False, 'reason': '3.19 尚未接入此项网页操作。'}
                    for name in ('currency', 'progression', 'inventory', 'story', 'skip_tutorial')}
    capabilities['launch'] = {'available': True, 'reason': '首次启动创建约 24 GB 隔离副本；登录可能需要数分钟。'}
    capabilities['launch_settings'] = {'available': True, 'reason': '玩家名、显示模式、分辨率、FOV 和帧率上限按安装保存，下次启动生效。'}
    capabilities['currency'] = {'available': True, 'reason': '增加本地档案余额，下次登录生效。',
                                'currency_label': 'GP', 'premium_label': 'CP'}
    capabilities['inventory'] = {'available': True, 'reason': '保存完整物品目录并保留已有库存；3.19 库存列表最多载入前 20,000 项，下次登录生效。'}
    capabilities['progression'] = {'available': True, 'reason': '当前版本最高 70 级、4 次转生；同步等级解锁条件。',
                                   'max_level': SCHEMA['max_level'], 'max_prestige': SCHEMA['max_prestige']}
    capabilities['story'] = {'available': True, 'reason': '解除 10 项剧情前置条件；地图启动与可玩性仍在恢复中。'}

    def __init__(self, root, selection, runtime):
        self.root, self.selection, self.runtime = Path(root), selection, Path(runtime)
        self.store = ConsoleStore(self.runtime)

    def environment(self):
        return {**os.environ, 'CODOL_GAME_ROOT': self.selection['path'],
                'CODOL_RUNTIME': str(self.runtime), 'CODOL_REPO_ROOT': str(self.root),
                'CODOL_VERSION_ROOT': str(VERSION_ROOT), 'PYTHONPATH': str(self.root)}

    def settings(self):
        return {'skip_tutorial': False, 'launch': read_options(self.runtime)}

    def set_settings(self, body):
        if set(body) != {'launch'}:
            raise ValueError('需要有效的启动选项')
        save_options(self.runtime, body['launch'])
        return self.settings()

    def profiles(self):
        return [self.store.summary()] if self.store.profile.exists() else []

    def inventory(self, uid):
        self.store.validate_user(uid)
        return self.store.inventory()

    def mutate(self, action, body):
        fields = {'currency': {'user_id', 'amount'}, 'premium': {'user_id', 'amount'},
                  'unlock': {'user_id'}, 'progression': {'user_id', 'level', 'prestige'},
                  'story': {'user_id'}}
        if action not in fields or set(body) != fields[action]:
            raise ValueError('需要有效的账号和操作参数')
        self.store.validate_user(body['user_id'])
        if action == 'unlock':
            return self.store.grant_all()
        if action == 'story':
            return self.store.unlock_story()
        if action == 'progression':
            return self.store.set_progression(body['level'], body['prestige'])
        return self.store.add_currency(body['amount'], '2' if action == 'premium' else '1')
