"""Loopback-only CODOL local protocol service; local artifacts live in runtime/."""
import json
import atexit
import socket
import ssl
import threading
from datetime import datetime, timezone
from pathlib import Path
from dw_auth import auth_reply
from dw_lobby import handle_lobby, stun_reply
from dw_profiles import ProfileStore
from dw_marketplace import MarketplaceStore
from dw_progression import PrivateProfileStore
from match_server.runtime import load_matchmaking

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / 'runtime'
LOCK = threading.Lock()
MATCHMAKING = None

def record(kind, **fields):
    event = {'time': datetime.now(timezone.utc).isoformat(), 'event': kind, **fields}
    line = json.dumps(event, ensure_ascii=False)
    with LOCK:
        with (RUNTIME / 'logs/server.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(line + '\n')
        print(line, flush=True)

def save_capture(kind, data):
    name = f'{datetime.now(timezone.utc):%Y%m%dT%H%M%S%f}-{kind}.bin'
    (RUNTIME / 'captures' / name).write_bytes(data)
    return name

def auth_client(sock, peer, context):
    try:
        sock.settimeout(15)
        with context.wrap_socket(sock, server_side=True) as conn:
            data = b''
            while b'\r\n\r\n' not in data:
                block = conn.recv(65536)
                if not block:
                    return
                data += block
            header, body = data.split(b'\r\n\r\n', 1)
            lines = header.decode('latin-1').split('\r\n')
            headers = dict(line.split(':', 1) for line in lines[1:] if ':' in line)
            if any(k.lower() == 'expect' and v.strip().lower() == '100-continue' for k, v in headers.items()):
                conn.sendall(b'HTTP/1.1 100 Continue\r\n\r\n')
            length = int(next((v for k, v in headers.items() if k.lower() == 'content-length'), '0'))
            while len(body) < length:
                block = conn.recv(min(65536, length - len(body)))
                if not block:
                    break
                body += block
            capture = save_capture('auth-request', header + b'\r\n\r\n' + body)
            try:
                request = json.loads(body)
                keys = list(request)
            except (ValueError, TypeError):
                keys = []
            record('auth_request', peer=peer, tls=conn.version(), cipher=conn.cipher(), request=lines[0], body_length=len(body), keys=keys, capture=capture)
            if lines[0].startswith('POST /auth/'):
                response = json.dumps(auth_reply(request), separators=(',', ':')).encode()
                status = b'200 OK'
                record('auth_reply', task=11, code=700, capture=save_capture('auth-reply', response))
            else:
                response = b'CODOL local service'
                status = b'200 OK'
            conn.sendall(b'HTTP/1.1 ' + status + b'\r\nContent-Type: application/json\r\nContent-Length: ' + str(len(response)).encode() + b'\r\nConnection: close\r\n\r\n' + response)
    except (OSError, ValueError) as error:
        record('auth_error', peer=peer, error=str(error))
        sock.close()

def lobby_client(sock, peer):
    try:
        with sock:
            sock.settimeout(120)
            handle_lobby(sock, peer, record, save_capture,
                         profiles=ProfileStore(RUNTIME / 'data/public-profiles'),
                         private_profiles=PrivateProfileStore(RUNTIME / 'data/private-profiles', RUNTIME / 'backups/private-profiles'),
                         marketplace=MarketplaceStore(RUNTIME / 'data/marketplace', RUNTIME / 'backups/marketplace'),
                         # Menu text is decoded as CP936 by the shipped client.
                         publisher_files={'mp_playlists_shipRetail_release.info':
                                          (ROOT / 'data/match-playlist.info').read_text('utf-8').encode('gbk')},
                         matchmaking=MATCHMAKING)
    except OSError as error:
        record('lobby_error', peer=peer, error=str(error))

def listen_stun():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as listener:
        listener.bind(('127.0.0.1', 3074))
        record('stun_listening', host='127.0.0.1', port=3074)
        while True:
            data, peer = listener.recvfrom(65536)
            record('stun_request', peer=peer, length=len(data), capture=save_capture('stun-request', data))
            response = stun_reply(data, peer, ('127.0.0.1', 3074))
            if response is not None:
                listener.sendto(response, peer)
                record('stun_reply', peer=peer, capture=save_capture('stun-reply', response))

def listen(port, handler):
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', port))
        listener.listen()
        record('listening', host='127.0.0.1', port=port)
        while True:
            sock, peer = listener.accept()
            threading.Thread(target=handler, args=(sock, peer), daemon=True).start()

if __name__ == '__main__':
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1
    context.set_ciphers('ALL:@SECLEVEL=0')
    context.options |= ssl.OP_NO_TICKET
    context.load_cert_chain(RUNTIME / 'certs/server.pem', RUNTIME / 'certs/server-key.pem')
    match_package = RUNTIME / 'match/nuketown'
    try:
        MATCHMAKING = load_matchmaking(match_package, record=record)
        atexit.register(MATCHMAKING.close)
        record('independent_match_ready', package=str(match_package), map=MATCHMAKING.map_name,
               gametype='dm', players=2, checksum=MATCHMAKING.options['netconst_checksum'])
    except (OSError, ValueError, KeyError) as error:
        record('independent_match_failed', error=str(error), package=str(match_package))
    threading.Thread(target=listen_stun, daemon=True).start()
    threading.Thread(target=listen, args=(3074, lobby_client), daemon=True).start()
    listen(443, lambda sock, peer: auth_client(sock, peer, context))
