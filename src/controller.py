"""Loopback-only control API and local documentation reader."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
import threading
from urllib.parse import parse_qs, urlsplit
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import importlib
from manager.installations import Installations
from manager.folder_picker import choose_folder


def game_running():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq codoMP_client_shipRetail.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, check=True)
    return b'codoMP_client_shipRetail.exe' in result.stdout


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def under(directory, name):
    path = (directory / name).resolve()
    if not path.is_relative_to(directory.resolve()):
        raise ValueError('路径必须位于指定目录内')
    return path


def create_server(root, port=8765, *, game_status=game_running, installations=None, choose_directory=choose_folder):
    root = Path(root).resolve()
    mutation_lock = threading.RLock()
    installs = installations or Installations(root)
    adapters = {}

    def adapter_for(selection):
        definition = installs.definition(selection)
        key = selection['instance_id']
        if key not in adapters:
            module = importlib.import_module(definition['adapter'])
            adapters[key] = module.Adapter(root, selection, installs.runtime(selection))
        return adapters[key]

    def command(adapter, name, action):
        return subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                               str(Path(adapter.environment()['CODOL_VERSION_ROOT']) / 'scripts' / name),
                               '-Action', action, '-PythonPath', sys.executable], env=adapter.environment(),
                              capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                              timeout=getattr(adapter, 'command_timeout', 120))

    def session_adapter():
        saved = root / 'config/session.json'
        selection = json.loads(saved.read_text(encoding='utf-8')) if saved.is_file() else installs.current()
        return adapter_for(selection) if selection['state'] == 'matched' else None

    def server_state():
        adapter = session_adapter()
        if adapter is None: return {'running': False, 'pid': None, 'ready': False, 'ports': []}
        result = command(adapter, 'Control-Services.ps1', 'status')
        if result.returncode: raise OSError(result.stderr.decode('utf-8', errors='replace'))
        return json.loads(result.stdout.decode('utf-8-sig'))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def reply(self, value, status=200):
            self.send_bytes(json.dumps(value, ensure_ascii=False).encode(), 'application/json; charset=utf-8', status)

        def send_bytes(self, data, content_type, status=200):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            self.dispatch(False)

        def do_POST(self):
            self.dispatch(True)

        def dispatch(self, writing):
            allowed = {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
            host = self.headers.get('Host', '')
            origin = self.headers.get('Origin')
            if host not in allowed or (origin and origin not in {'http://' + h for h in allowed}):
                self.reply({'error': '只接受本机同源请求'}, 403)
                return
            try:
                url = urlsplit(self.path)
                query = parse_qs(url.query)
                if writing:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 8192 or self.headers.get_content_type() != 'application/json':
                        raise ValueError('需要有效的 JSON 请求')
                    body = json.loads(self.rfile.read(length))
                    if not isinstance(body, dict):
                        raise ValueError('请求必须是对象')
                if url.path == '/api/versions' and not writing:
                    self.reply({'versions': [{'game_id': v['game_id'], 'version': v['version'],
                        'label': v.get('label', v['version']), 'supported': bool(v.get('adapter'))} for v in installs.catalog]})
                elif url.path in ('/api/installation/select', '/api/installation/choose') and writing:
                    choosing = url.path.endswith('/choose')
                    if set(body) != (set() if choosing else {'path'}):
                        raise ValueError('需要有效的游戏目录参数')
                    if game_status():
                        self.reply({'error': '请先停止游戏与模拟服务器，再切换目录'}, 409); return
                    path = choose_directory() if choosing else body['path']
                    if path is None:
                        self.reply({'cancelled': True, 'installation': installs.current()}); return
                    with mutation_lock:
                        if game_status() or server_state()['running']:
                            self.reply({'error': '请先停止游戏与模拟服务器，再切换目录'}, 409); return
                        selection = installs.select(path, prepare=True)
                    self.reply({'cancelled': False, 'installation': selection})
                elif url.path == '/api/status' and not writing:
                    with mutation_lock:
                        selection = installs.current()
                        adapter = adapter_for(selection) if selection['state'] == 'matched' else None
                        self.reply({'installation': selection, 'profiles': adapter.profiles() if adapter else [],
                                    'game_running': game_status(), 'capabilities': adapter.capabilities if adapter else {}})
                elif url.path == '/api/server/status' and not writing:
                    with mutation_lock: self.reply(server_state())
                elif url.path == '/api/settings' or (url.path == '/api/inventory' and not writing) or (url.path.startswith('/api/profile/') and writing) or (url.path in ('/api/game/launch', '/api/game/stop') and writing):
                    with mutation_lock:
                        selection = installs.current(fresh=writing)
                        stopping = url.path == '/api/game/stop'
                        adapter = session_adapter() if stopping else (adapter_for(selection) if selection['state'] == 'matched' else None)
                        if not adapter:
                            if url.path == '/api/settings' and not writing:
                                self.reply({'skip_tutorial': True}); return
                            self.reply({'error': selection['reason']}, 409); return
                        capability = {'/api/game/launch': 'launch', '/api/settings': 'skip_tutorial'}.get(url.path)
                        if writing and capability and not adapter.capabilities.get(capability, {}).get('available'):
                            self.reply({'error': '当前版本尚未支持此操作'}, 409); return
                        if url.path == '/api/settings':
                            self.reply(adapter.set_settings(body) if writing else adapter.settings())
                        elif url.path == '/api/inventory':
                            self.reply(adapter.inventory(query.get('user_id', [''])[0]))
                        elif url.path.startswith('/api/profile/'):
                            action = url.path.rsplit('/', 1)[1]
                            capability = {'currency':'currency', 'premium':'currency', 'progression':'progression',
                                          'renew':'inventory', 'unlock':'inventory', 'story':'story'}.get(action)
                            if not adapter.capabilities.get(capability, {}).get('available'):
                                self.reply({'error': '此项数据结构尚未验证，未修改档案'}, 409); return
                            if game_status():
                                self.reply({'error': '请先退出游戏，再修改玩家数据'}, 409); return
                            self.reply({**adapter.mutate(action, body), 'message': '玩家数据已保存；重新启动游戏后生效。'})
                        else:
                            if body: raise ValueError('游戏操作不接受参数')
                            launching = not stopping
                            if launching and game_status():
                                self.reply({'error': '游戏已运行，请先退出当前游戏'}, 409); return
                            if launching:
                                installs.prepare(selection)
                                write_json(root / 'config/session.json', selection)
                            result = command(adapter, 'Control-Game.ps1', 'start' if launching else 'stop')
                            if result.returncode:
                                self.reply({'error': '游戏与服务器操作失败', 'detail': result.stderr.decode('utf-8', errors='replace')}, 500); return
                            if game_status() != launching:
                                self.reply({'error': '启动未完成，游戏未运行。' if launching else '停止未完成，游戏仍在运行。'}, 500); return
                            if stopping: (root / 'config/session.json').unlink(missing_ok=True)
                            self.reply({'message': '游戏与服务器已启动。' if launching else '游戏与服务器已停止。'})
                elif url.path == '/api/docs' and not writing:
                    directory = root / 'docs'
                    files = [{'path': p.relative_to(directory).as_posix(), 'size': p.stat().st_size}
                             for p in sorted(directory.rglob('*'))
                             if p.is_file() and p.resolve().is_relative_to(directory.resolve())]
                    self.reply({'files': files})
                elif url.path == '/api/docs/file' and not writing:
                    name = query.get('path', [''])[0]
                    path = under(root / 'docs', name)
                    self.reply({'path': name, 'content': path.read_text(encoding='utf-8-sig')})
                elif not writing and not url.path.startswith('/api/'):
                    path = under(root / 'web/dist', url.path.lstrip('/') or 'index.html')
                    self.send_bytes(path.read_bytes(), mimetypes.guess_type(path)[0] or 'application/octet-stream')
                else:
                    self.reply({'error': '接口不存在'}, 404)
            except (ValueError, UnicodeError) as error:
                self.reply({'error': str(error)}, 400)
            except (FileNotFoundError, IsADirectoryError):
                self.reply({'error': '文件不存在'}, 404)
            except OSError as error:
                self.reply({'error': str(error)}, 500)
            except subprocess.SubprocessError as error:
                self.reply({'error': str(error)}, 500)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = create_server(Path(__file__).resolve().parents[1], args.port)
    print(f'Controller: http://127.0.0.1:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
