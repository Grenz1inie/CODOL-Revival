"""3.19.26.22 startup integration; profile editing is not yet validated."""
import os
from pathlib import Path

VERSION_ROOT = Path(__file__).resolve().parent


class Adapter:
    command_timeout = 600  # First copy plus the original client's login delay.
    capabilities = {name: {'available': False, 'reason': '3.19 当前仅接入启动与本地大厅。'}
                    for name in ('currency', 'progression', 'inventory', 'story', 'skip_tutorial')}
    capabilities['launch'] = {'available': True, 'reason': '首次启动创建约 24 GB 隔离副本；登录可能需要数分钟。'}

    def __init__(self, root, selection, runtime):
        self.root, self.selection, self.runtime = Path(root), selection, Path(runtime)

    def environment(self):
        return {**os.environ, 'CODOL_GAME_ROOT': self.selection['path'],
                'CODOL_RUNTIME': str(self.runtime), 'CODOL_REPO_ROOT': str(self.root),
                'CODOL_VERSION_ROOT': str(VERSION_ROOT), 'PYTHONPATH': str(self.root)}

    def settings(self):
        return {'skip_tutorial': False}

    def profiles(self):
        return []

    def inventory(self, uid):
        raise ValueError('3.19 物品编辑尚未接入')
