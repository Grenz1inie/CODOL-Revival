"""Loopback-only control API and local documentation reader."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import threading
from urllib.parse import parse_qs, urlsplit
from dw_profiles import validate_profile
from dw_marketplace import MarketplaceStore
from dw_progression import PrivateProfileStore

CAPABILITIES = {
    'progression': {'available': True, 'reason': '此版本上限为 3 转生、70 级；同时更新商城等级解锁值。'},
    'currency': {'available': True, 'reason': '游戏币与点券独立保存；退出游戏后修改，重登生效。'},
    'inventory': {'available': True, 'reason': '发放 6772 种物品（含配件与皮肤），武器使用满级经验；永久保存，已有数量不叠加。'},
}


def game_running():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq codoMP_client_shipRetail.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10, check=True)
    return b'codoMP_client_shipRetail.exe' in result.stdout


def read_settings(root):
    path = root / 'runtime/data/controller.json'
    if not path.exists():
        return {'skip_tutorial': True}
    return json.loads(path.read_text(encoding='utf-8'))


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


def create_server(root, port=8765, *, game_status=game_running):
    root = Path(root).resolve()
    mutation_lock = threading.Lock()
    marketplace = MarketplaceStore(root / 'runtime/data/marketplace', root / 'runtime/backups/marketplace')
    progression = PrivateProfileStore(root / 'runtime/data/private-profiles', root / 'runtime/backups/private-profiles')

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
                if url.path == '/api/settings':
                    if writing:
                        if set(body) != {'skip_tutorial'} or type(body['skip_tutorial']) is not bool:
                            raise ValueError('skip_tutorial 必须是布尔值')
                        with mutation_lock:
                            write_json(root / 'runtime/data/controller.json', body)
                    self.reply(read_settings(root))
                elif url.path == '/api/status' and not writing:
                    profiles = []
                    for path in sorted((root / 'runtime/data/public-profiles').glob('*.bin')):
                        if re.fullmatch('[0-9a-f]{16}', path.stem):
                            validate_profile(path.read_bytes())
                            profiles.append({'user_id': path.stem, 'currency': marketplace.balance(int(path.stem, 16)),
                                             'premium': marketplace.balance(int(path.stem, 16), currency_id=2),
                                             **progression.summary(int(path.stem, 16))})
                    self.reply({'profiles': profiles, 'game_running': game_status(), 'capabilities': CAPABILITIES})
                elif url.path == '/api/game/launch' and writing:
                    with mutation_lock:
                        if game_status():
                            self.reply({'error': '游戏已运行，请先退出当前游戏'}, 409)
                            return
                        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                                 str(root / 'scripts/Launch-Game.ps1')], capture_output=True,
                                                creationflags=subprocess.CREATE_NO_WINDOW, timeout=90)
                        if result.returncode:
                            self.reply({'error': result.stderr.decode('utf-8', errors='replace')}, 500)
                            return
                    self.reply({'message': '游戏已启动；界面与等级以游戏实际显示为准。'})
                elif url.path == '/api/inventory' and not writing:
                    uid = query.get('user_id', [''])[0]
                    if not re.fullmatch('[0-9a-f]{16}', uid):
                        raise ValueError('需要有效账号')
                    validate_profile((root / 'runtime/data/public-profiles' / (uid + '.bin')).read_bytes())
                    catalogue = json.loads((Path(__file__).resolve().parents[1] / 'data/marketplace-catalog.json').read_text(encoding='utf-8'))['items']
                    self.reply({'items': [{**item, 'name': catalogue.get(str(item['item_id']), {}).get('name', str(item['item_id']))}
                                          for item in marketplace.inventory(int(uid, 16))]})
                elif url.path in ('/api/profile/currency', '/api/profile/premium', '/api/profile/progression', '/api/profile/renew', '/api/profile/unlock', '/api/profile/story') and writing:
                    action = url.path.rsplit('/', 1)[1]
                    fields = {'currency': {'user_id', 'amount'}, 'premium': {'user_id', 'amount'},
                              'progression': {'user_id', 'level', 'prestige'},
                              'renew': {'user_id', 'item_id', 'days'}, 'unlock': {'user_id'}, 'story': {'user_id'}}[action]
                    if (set(body) != fields or not isinstance(body['user_id'], str)
                            or not re.fullmatch('[0-9a-f]{16}', body['user_id'])):
                        raise ValueError('需要有效的账号和操作参数')
                    with mutation_lock:
                        path = root / 'runtime/data/public-profiles' / (body['user_id'] + '.bin')
                        validate_profile(path.read_bytes())
                        if game_status():
                            self.reply({'error': '请先退出游戏，再修改玩家数据'}, 409)
                            return
                        user_id = int(body['user_id'], 16)
                        if action in ('currency', 'premium'):
                            currency_id = 2 if url.path.endswith('/premium') else 1
                            result = {marketplace.currency_key(currency_id): marketplace.add_currency(
                                user_id, body['amount'], currency_id=currency_id)}
                        elif action == 'renew':
                            result = marketplace.renew(user_id, body['item_id'], body['days'])
                        elif action == 'unlock':
                            result = marketplace.grant_all(user_id)
                        elif action == 'story':
                            result = progression.unlock_story(user_id)
                        else:
                            result = progression.set_progression(user_id, body['level'], body['prestige'])
                    self.reply({**result, 'message': '玩家数据已保存；重新启动游戏后生效。'})
                elif url.path.startswith('/api/profile/') and writing:
                    self.reply({'error': '此项数据结构尚未验证，未修改档案'}, 409)
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
