"""Prepare a private game copy for the supplied 3.19 offline loader."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess

from .settings import read_options

CLIENT = 'codoMP_client_shipRetail.exe'
CLIENT_SHA256 = '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537'
LOADER = 'loader/Client-english-fixed-resources.exe'
REQUIRED = ('patches/localization.txt', 'patches/ff_init_common_gfx_V109.ifs',
            'server/match-host/version.dll', 'server/match-host/client_loopback319.dll', 'server/' + LOADER)
NATIVE_HASHES = {
    'server/' + LOADER: 'bd89f07fd634498f37be10c420915ba0581c6cdd661b8567aecfaac809c70867',
    'server/match-host/version.dll': 'b9e297174c9c652f10835ee39cd001b9c85e1fd4b70813adf4dafddc653dc97d',
    'server/match-host/client_loopback319.dll': 'ffc616e8534b31292cedabf48e31d4f6915693f63a8503414b26622adf894e56',
}


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


def import_package(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    for relative in REQUIRED:
        if not (source / relative).is_file():
            raise FileNotFoundError(f'缺少 3.19 启动组件：{relative}')
    for relative, expected in NATIVE_HASHES.items():
        if digest(source / relative) != expected:
            raise ValueError(f'启动组件指纹不匹配：{relative}')
    for name in ('server', 'patches'):
        shutil.copytree(source / name, destination / name, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('*.py', '__pycache__', '*.log', '*.jsonl', '*.dmp'))
    return destination


def prepare(source, runtime, package, system_version=None):
    source, runtime, package = map(lambda p: Path(p).resolve(), (source, runtime, package))
    game = runtime / 'game'
    check_client(source)
    language = read_options(runtime)['game_language']
    resources = [(package / 'patches' / Path(relative).name if language == 'en' else source / relative,
                  game / relative, True)
                 for relative in ('localization.txt', 'IIPS/IIPSDownload/ff_init_common_gfx_V109.ifs')]
    # Both the loader and its proxy use ANSI paths and MAX_PATH buffers.
    if not str(runtime).isascii() or len(str(game / CLIENT)) >= 260:
        raise ValueError('3.19 加载器需要较短的纯英文工具目录')
    if runtime == source or runtime.is_relative_to(source):
        raise ValueError('运行目录不能位于原游戏目录内')
    system_version = Path(system_version) if system_version else Path(os.environ['SystemRoot']) / 'SysWOW64/version.dll'
    for path in [*(package / p for p in REQUIRED if not p.startswith('patches/')),
                 *(src for src, _, _ in resources), system_version]:
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
    if not ready.exists():
        shutil.copytree(source, game, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('Cross', '.codegraph', '__pycache__'))
        check_client(game)
        ready.write_text(CLIENT_SHA256, encoding='ascii')
    check_client(game)
    # Populate missing assets only. Reopening must not reset profile, wallet or saves.
    for src in (package / 'server').rglob('*'):
        if src.is_file():
            dst = runtime / 'server' / src.relative_to(package / 'server')
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    for src, dst, backup in (
        (package / 'server/match-host/version.dll', game / 'version.dll', False),
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
    parser.add_argument('--launcher', required=True, type=Path)
    parser.add_argument('--package', required=True, type=Path)
    args = parser.parse_args()
    print(import_package(args.launcher, args.package))
