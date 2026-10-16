"""Identify local CODOL installations without executing or changing game files."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from xml.etree import ElementTree


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


class Installations:
    def __init__(self, root, *, catalog=None):
        self.root = Path(root).resolve()
        self.catalog = catalog if catalog is not None else json.loads(
            (self.root / 'games/codol/versions.json').read_text(encoding='utf-8'))
        self.file = self.root / 'config/installation.json'
        self._hashes = {}

    def detect(self, path, *, fresh=False):
        if not isinstance(path, str) or not path.strip() or not Path(path).is_absolute():
            raise ValueError('需要有效的游戏目录绝对路径')
        game = Path(path).resolve()
        result = {'path': str(game), 'game_id': 'codol', 'version': None,
                  'state': 'invalid', 'reason': '请选择包含游戏主程序的目录'}
        if not game.is_dir():
            return result
        versions = []
        try:
            ini = game / 'IIPS/IIPSVersion.ini'
            xml = game / 'TCLS/mmog_data.xml'
            if ini.is_file():
                versions.append(ini.read_text(encoding='utf-8-sig').strip())
            if xml.is_file():
                raw = xml.read_bytes()
                encoding = 'gb18030' if re.search(br'encoding=[\"\'](?:gb2312|gbk|gb18030)[\"\']', raw[:150], re.I) else 'utf-8-sig'
                document = ElementTree.fromstring(raw.decode(encoding))
                versions.append(document.findtext('./ClientConf/VersionData/Version', '').strip())
        except (OSError, UnicodeError, ElementTree.ParseError):
            result['reason'] = '版本文件无法读取或格式损坏'
            return result
        if not versions or any(not re.fullmatch(r'\d+\.\d+\.\d+\.\d+', v) for v in versions):
            result['reason'] = '未找到有效的版本号'
            return result
        if len(set(versions)) != 1:
            result['reason'] = '两个版本文件的版本号不一致'
            return result
        result['version'] = versions[0]
        definition = next((v for v in self.catalog if v['version'] == versions[0]), None)
        if definition is None:
            return {**result, 'state': 'unknown', 'reason': '该版本尚未收录'}
        executable = game / definition['executable']
        if not executable.is_file():
            result['reason'] = '游戏主程序不存在'
            return result
        if not definition.get('adapter'):
            return {**result, 'state': 'unsupported', 'reason': '版本已识别，适配逻辑尚未接入'}
        try:
            stat = executable.stat()
            key = (str(executable), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
            if fresh or key not in self._hashes:
                with executable.open('rb') as stream:
                    self._hashes[key] = hashlib.file_digest(stream, 'sha256').hexdigest()
            digest = self._hashes[key]
        except OSError:
            return {**result, 'reason': '无法读取游戏主程序'}
        if digest != definition['sha256']:
            return {**result, 'state': 'fingerprint_mismatch', 'reason': '主程序指纹与已适配客户端不一致'}
        identity = hashlib.sha256(os.path.normcase(str(game)).encode('utf-8')).hexdigest()[:12]
        return {**result, 'state': 'matched', 'reason': '已匹配',
                'instance_id': f"codol-{versions[0]}-{identity}"}

    def current(self, *, fresh=False):
        if not self.file.is_file():
            return {'state': 'unselected', 'path': '', 'version': None, 'reason': '请先选择游戏目录'}
        try:
            return self.detect(json.loads(self.file.read_text(encoding='utf-8'))['path'], fresh=fresh)
        except (OSError, ValueError, KeyError, TypeError):
            return {'state': 'invalid', 'path': '', 'version': None, 'reason': '目录配置无法读取，请重新选择游戏目录'}

    def select(self, path, *, prepare=False):
        result = self.detect(path, fresh=True)
        if prepare and result['state'] == 'matched':
            self.prepare(result)
        write_json(self.file, {'path': result['path']})
        return result

    def definition(self, selection):
        if selection['state'] != 'matched':
            raise ValueError(selection['reason'])
        return next(v for v in self.catalog if v['version'] == selection['version'])

    def runtime(self, selection):
        self.definition(selection)
        return self.root / 'runtime/instances' / selection['instance_id']

    def prepare(self, selection):
        """Copy legacy player data once, only for the original installation."""
        runtime = self.runtime(selection)
        if (runtime / 'instance.json').exists():
            return runtime
        runtime.parent.mkdir(parents=True, exist_ok=True)
        legacy = self.root / 'runtime'
        original = self.root.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z'
        # Stage before publishing: interruption never leaves a partly imported profile.
        with tempfile.TemporaryDirectory(prefix='import-', dir=runtime.parent) as temporary:
            stage = Path(temporary) / 'instance'
            stage.mkdir()
            names = ['certs']
            if Path(selection['path']) == original and selection['version'] == '3.3.3.3':
                names += ['data', 'backups']
            for name in names:
                if (legacy / name).is_dir(): shutil.copytree(legacy / name, stage / name)
            write_json(stage / 'instance.json', selection)
            stage.rename(runtime)
        return runtime
