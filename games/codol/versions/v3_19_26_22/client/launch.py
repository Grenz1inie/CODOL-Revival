"""Manage one 3.19 game session, including its owned local services."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

ROOT = Path(__file__).resolve().parents[5]
VERSION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from games.codol.versions.v3_19_26_22.client.lifecycle import Services, alive, identity, lobby_ready, service_status
from games.codol.versions.v3_19_26_22.client.preparation import CLIENT, NATIVE_HASHES, check_client, digest, grant_runtime_access, prepare
from games.codol.versions.v3_19_26_22.client.settings import apply_options, read_options
from games.codol.versions.v3_19_26_22.client.match import MatchSession

def save(runtime, state):
    temporary = runtime / 'startup.tmp'
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding='utf-8')
    temporary.replace(runtime / 'startup.json')


def read(runtime):
    path = runtime / 'startup.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def status(runtime):
    state = read(runtime)
    services = service_status(state.get('services', []))
    supervisor = alive(state.get('supervisor', {}))
    game_running = supervisor and alive(state.get('game', {}))
    match = state.get('match', {'phase': 'waiting', 'error': ''})
    match_service = service_status([match['service']] if match.get('service') else [])
    return {**services, 'running': services['running'] or supervisor,
            'ports': services['ports'] + match_service['ports'],
            'pid': state['supervisor']['pid'] if supervisor else None,
            'phase': state.get('phase', 'stopped'), 'error': state.get('error', '') or match.get('error', ''),
            'game_running': game_running,
            'match': {**match, 'ready': game_running and match_service['ready']},
            'lobby_ready': game_running and state.get('phase') == 'lobby'}


def elevate(runtime):
    python = Path(sys.executable).with_name('pythonw.exe')
    if not python.exists():
        python = Path(sys.executable)
    call = ctypes.windll.shell32.ShellExecuteW
    call.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
                     ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int]
    call.restype = ctypes.c_void_p
    arguments = subprocess.list2cmdline(['-B', str(Path(__file__).resolve()), 'supervise', '--runtime', str(runtime)])
    if (call(None, 'runas', str(python), arguments, str(ROOT), 0) or 0) <= 32:
        raise OSError('UAC 授权未完成，3.19 游戏尚未启动')


def stop(runtime):
    if not status(runtime)['running']:
        return
    (runtime / 'stop.request').touch()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if not status(runtime)['running']:
            return
        time.sleep(0.2)
    raise TimeoutError('3.19 会话未停止，请查看运行目录中的日志')


def start(source, runtime):
    if status(runtime)['running']:
        raise ValueError('此安装的游戏或服务仍在运行，请先停止')
    prepare(source, runtime, ROOT / 'runtime/packages/codol-3.19.26.22')
    (runtime / 'stop.request').unlink(missing_ok=True)
    save(runtime, {'phase': 'pending'})
    elevate(runtime)
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        state = status(runtime)
        if state['game_running']:
            return
        if state['phase'] in ('error', 'stopped'):
            raise RuntimeError(state['error'] or '游戏在登录大厅前退出，请重试并查看 logs')
        time.sleep(0.5)
    (runtime / 'stop.request').touch()
    raise TimeoutError('等待游戏进程创建超时，请查看运行目录中的 logs')


def supervise(runtime):
    state = {'phase': 'starting', 'supervisor': identity(os.getpid()), 'services': []}
    loader = None
    services = None
    match = None
    try:
        save(runtime, state)
        game = runtime / 'game'
        check_client(game)
        for relative, expected in NATIVE_HASHES.items():
            if digest(runtime / relative) != expected:
                raise ValueError(f'启动组件指纹不匹配：{relative}')
        # Logs from a previous elevated run may predate the inherited user ACL.
        for directory in (runtime / 'logs', runtime / 'server'):
            for path in directory.rglob('*'):
                if path.is_file() and path.suffix in ('.log', '.jsonl'):
                    grant_runtime_access(path)
        python = str(Path(sys.executable).with_name('python.exe'))
        env = {**os.environ, 'CODOL319_GAME_DIR': str(game),
               'CODOL319_SERVER_ROOT': str(runtime / 'server'), 'PYTHONUTF8': '1',
               'CODOL319_EXTRA_ARGS': apply_options(runtime)}
        specs = [{'name': name, 'port': port,
                  'command': [python, '-B', '-X', 'utf8', str(VERSION / 'server' / script), *args]}
                 for name, port, script, args in (
                    ('auth', 31900, 'auth_capture.py', ['--http', '--local-response']),
                    ('lobby', 31901, 'lsg_handshake.py', ['--room-probe', '--inventory-keyed', '--ayria-parity']),
                    ('web', 8319, 'nfs_http319.py', ['8319']))]
        services = Services(runtime, specs, env)
        services.start()
        state.update(services=services.records, phase='launching')
        save(runtime, state)
        since = time.time()
        language_args = ['--english-resources'] if read_options(runtime)['game_language'] == 'en' else []
        with (runtime / 'logs/loader.log').open('ab') as out:
            loader = subprocess.Popen([python, '-B', '-X', 'utf8', str(VERSION / 'client/loader.py'), *language_args],
                cwd=runtime, env=env, stdin=subprocess.DEVNULL,
                stdout=out, stderr=subprocess.STDOUT, close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)
        state['loader'] = identity(loader.pid)
        save(runtime, state)
        deadline = time.monotonic() + 60
        while loader.poll() is None and not (runtime / 'stop.request').exists():
            if any(p.poll() is not None for p in services.processes):
                raise RuntimeError('本地服务退出，请查看 logs')
            if 'game' not in state:
                for child in psutil.Process(loader.pid).children(recursive=True):
                    if os.path.normcase(child.exe()) == os.path.normcase(str(game / CLIENT)):
                        state['game'] = identity(child.pid)
                        match = MatchSession(runtime, state['game'], since)
                        state['match'] = match.snapshot()
                        save(runtime, state)
                        break
            if state['phase'] != 'lobby':
                if alive(state.get('game', {})) and lobby_ready(runtime / 'server/lsg-handshake.jsonl', since):
                    state['phase'] = 'lobby'
                    save(runtime, state)
                elif 'game' not in state and time.monotonic() >= deadline:
                    raise TimeoutError('加载器未创建游戏进程，请查看 logs/loader.log')
            if state['phase'] == 'lobby' and match is not None:
                match_state = match.poll()
                if match_state != state.get('match'):
                    state['match'] = match_state
                    save(runtime, state)
            time.sleep(0.5)
        if state['phase'] != 'lobby' and not (runtime / 'stop.request').exists():
            raise RuntimeError('游戏在登录前退出，请重试并查看 logs/loader.log')
        state['phase'] = 'stopped'
    except Exception as error:
        state.update(phase='error', error=str(error))
    finally:
        try:
            if match is not None:
                match.close()
                state['match'] = match.snapshot()
        finally:
            try:
                if loader is not None and loader.poll() is None:
                    subprocess.run(['taskkill', '/PID', str(loader.pid), '/T', '/F'],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                    loader.wait(timeout=10)
            finally:
                if services is not None:
                    services.close()
                save(runtime, state)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'stop', 'status', 'supervise'))
    parser.add_argument('--runtime', required=True, type=Path)
    parser.add_argument('--source', type=Path)
    args = parser.parse_args()
    try:
        if args.action == 'start':
            if args.source is None:
                raise ValueError('需要 --source 游戏目录')
            start(args.source.resolve(), args.runtime.resolve())
        elif args.action == 'stop':
            stop(args.runtime.resolve())
        elif args.action == 'supervise':
            supervise(args.runtime.resolve())
        else:
            print(json.dumps(status(args.runtime.resolve()), ensure_ascii=True))
    except Exception as error:
        if sys.stderr is not None:
            print(str(error), file=sys.stderr)
        sys.exit(1)
