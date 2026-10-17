"""Prepare a private game copy using source builds and the original 3.19 game."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess

from .settings import read_options
from . import boot_assets, native_build

CLIENT = 'codoMP_client_shipRetail.exe'
CLIENT_SHA256 = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_client(game):
    if digest(game / CLIENT) != CLIENT_SHA256:
        raise ValueError('3.19.26.22 主程序指纹不匹配')


def grant_runtime_access(runtime):
    if os.name != 'nt':
        return
    # TemporaryDirectory inherits OWNER RIGHTS; elevated children may be owned by
    # Administrators. Keep the controller's user able to read/write this instance.
    result = subprocess.run(['whoami', '/user', '/fo', 'csv', '/nh'], capture_output=True,
                            creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    sid = re.search(rb'S-1-5-(?:\d+-)+\d+', result.stdout).group().decode('ascii')
    rights = '(OI)(CI)M' if runtime.is_dir() else 'M'
    subprocess.run(['icacls', str(runtime), '/grant', f'*{sid}:{rights}'],
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True)


def prepare(source, runtime, system_version=None):
    source, runtime = map(lambda p: Path(p).resolve(), (source, runtime))
    game = runtime / 'game'
    check_client(source)
    language = read_options(runtime)['game_language']
    resource_names = ('localization.txt', boot_assets.ARCHIVE)
    # Both the loader and its proxy use ANSI paths and MAX_PATH buffers.
    if not str(runtime).isascii() or len(str(game / CLIENT)) >= 260:
        raise ValueError('3.19 加载器需要较短的纯英文工具目录')
    if runtime == source or runtime.is_relative_to(source):
        raise ValueError('运行目录不能位于原游戏目录内')
    system_version = Path(system_version) if system_version else Path(os.environ['SystemRoot']) / 'SysWOW64/version.dll'
    for path in [*(source / p for p in resource_names), system_version]:
        if not path.is_file():
            raise FileNotFoundError(f'缺少 3.19 启动组件：{path}')
    ready = runtime / 'game-copy.ready'
    if not ready.exists():
        required = 0
        for path in source.rglob('*'):
            if path.is_file():
                target = game / path.relative_to(source)
                required += max(0, path.stat().st_size - (target.stat().st_size if target.is_file() else 0))
        volume = next(p for p in (runtime, *runtime.parents) if p.exists())
        if shutil.disk_usage(volume).free < required + 256 * 1024 * 1024:
            raise OSError('磁盘空间不足，首次启动需要约 24 GB 的隔离副本')
    runtime.mkdir(parents=True, exist_ok=True)
    grant_runtime_access(runtime)
    native = native_build.build(runtime / 'server/match-host')
    generated = boot_assets.build(source, runtime / 'generated/boot319', native)
    resources = [(generated / 'patches' / Path(relative).name if language == 'en' else source / relative,
                  game / relative, True) for relative in resource_names]
    for src, _, _ in resources:
        if not src.is_file():
            raise FileNotFoundError(f'缺少生成的 3.19 资源：{src}')
    if not ready.exists():
        shutil.copytree(source, game, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('Cross', '.codegraph', '__pycache__'))
        check_client(game)
        ready.write_text(CLIENT_SHA256, encoding='ascii')
    check_client(game)
    # Only generated service resources belong here. Player state is never imported.
    for folder in ('publisher-files', 'match-host/nfs-www'):
        for src in (generated / folder).rglob('*'):
            if src.is_file():
                dst = runtime / 'server' / src.relative_to(generated)
                dst.parent.mkdir(parents=True, exist_ok=True)
                if not dst.exists() or digest(src) != digest(dst):
                    shutil.copy2(src, dst)
    for src, dst, backup in (
        (native / 'version.dll', game / 'version.dll', False),
        (system_version, game / 'version_system319.dll', False),
        *resources,
    ):
        if dst.is_file() and digest(src) == digest(dst):
            continue
        if backup and dst.exists() and not dst.with_name(dst.name + '.original').exists():
            shutil.copy2(dst, dst.with_name(dst.name + '.original'))
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    (game / 'codol319-root.txt').write_text(str(runtime / 'server/match-host') + '\\\n', encoding='ascii')
    (runtime / 'server/match-host/arm-loopback319.txt').write_text('0', encoding='ascii')
    return game


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--runtime', required=True, type=Path)
    args = parser.parse_args()
    print(prepare(args.source, args.runtime))
