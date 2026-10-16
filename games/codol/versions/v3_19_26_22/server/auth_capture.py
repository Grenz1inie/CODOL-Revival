"""Bounded HTTPS diagnostic on loopback only; records requests, returns 503."""
from pathlib import Path
import os
import ssl,socket,time,json,sys
root=Path(os.environ['CODOL319_SERVER_ROOT'])
sys.path.insert(0,str(root))
def emit(event,**values):
    with (root/'auth-capture.jsonl').open('a',encoding='utf-8') as out:
        out.write(json.dumps(dict(event=event,time=time.time(),**values))+'\n')
ctx=None
if '--http' not in sys.argv:
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(root/'localhost-capture-cert.pem',root/'localhost-capture-key.pem')
s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
port=int(sys.argv[sys.argv.index('--port')+1]) if '--port' in sys.argv else 31900
s.bind(('127.0.0.1',port));s.listen(4);s.settimeout(1)
emit('listening',port=s.getsockname()[1])
# Runs until stopped (the old 2-hour limit cut off logins mid-launch); --lifetime N restores a limit.
deadline=time.monotonic()+(float(sys.argv[sys.argv.index("--lifetime")+1]) if "--lifetime" in sys.argv else float("inf"))
while time.monotonic()<deadline:
    try:c,peer=s.accept()
    except TimeoutError:continue
    emit('connection',peer=peer);c.settimeout(15)
    try:
        with (c if '--http' in sys.argv else ctx.wrap_socket(c,server_side=True)) as conn:
            emit('http_ready' if '--http' in sys.argv else 'tls_ready',version=None if '--http' in sys.argv else conn.version())
            data=b''
            while len(data)<65536:
                part=conn.recv(4096)
                if not part:break
                data+=part
                if b'\r\n\r\n' in data:
                    headers,body=data.split(b'\r\n\r\n',1)
                    size=next((int(x.split(b':',1)[1].strip()) for x in headers.split(b'\r\n') if x.lower().startswith(b'content-length:')),0)
                    if len(body)>=size:break
            if not data:
                emit('readiness_connection_closed');continue
            if b'\r\n\r\n' not in data:
                emit('invalid_http_request',bytes=len(data));continue
            emit('request',bytes=len(data),text=data.decode('utf-8',errors='replace'))
            if '--local-response' in sys.argv:
                from local_auth_ticket import response
                reply=response(json.loads(data.split(b'\r\n\r\n',1)[1]))
                body=json.dumps(reply).encode();status=b'200 OK';emit('synthetic_auth_response',bytes=len(body))
            else:
                body=b'{"diagnostic":"compatible local auth response not implemented"}';status=b'503 Service Unavailable'
            conn.sendall(b'HTTP/1.1 '+status+b'\r\nContent-Type: application/json\r\nConnection: close\r\nContent-Length: '+str(len(body)).encode()+b'\r\n\r\n'+body)
    except (OSError,ssl.SSLError,ValueError,IndexError) as ex:
        emit('connection_error',error=str(ex));c.close()
s.close();emit('stopped')
