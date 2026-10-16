"""Authenticated requests to the production lobby on an isolated ephemeral port."""
import hashlib
import hmac
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys

from games.codol.versions.v3_19_26_22.server import lsg_codec as codec


def connect_lobby(test, root):
    script = '''
import runpy, socket
class TestSocket(socket.socket):
    def bind(self, address): super().bind(('127.0.0.1', 0))
    def listen(self, count):
        super().listen(count)
        print(self.getsockname()[1], flush=True)
socket.socket = TestSocket
runpy.run_path('lsg_handshake.py', run_name='__main__')
'''
    process = subprocess.Popen([sys.executable, '-B', '-c', script],
        cwd=Path(__file__).resolve().parents[1] / 'server',
        env={**os.environ, 'CODOL319_SERVER_ROOT': str(root)},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    test.addCleanup(process.stdout.close)
    test.addCleanup(process.stderr.close)
    def stop():
        process.terminate()
        process.wait(timeout=5)
    test.addCleanup(stop)
    port = int(process.stdout.readline())
    connection = socket.create_connection(('127.0.0.1', port), timeout=5)
    test.addCleanup(connection.close)

    def exact(count):
        data = b''
        while len(data) < count:
            chunk = connection.recv(count-len(data))
            test.assertTrue(chunk, 'Lobby closed before replying')
            data += chunk
        return data

    def frame():
        head = exact(4)
        return head + exact(struct.unpack('<I', head)[0])

    hello = struct.pack('<4I', 200, 200, 210, 220) + bytes(12)
    connection.sendall(hello)
    greeting = frame()
    auth = b'\xab\x82' + b'isolated-test'
    framed = struct.pack('<I', len(auth)+8) + auth
    prk = hmac.new(hashlib.sha1(hello[8:]+greeting+framed).digest(),
                   b'Local319DiagnosticKey123', hashlib.sha1).digest()
    challenges = hmac.new(prk, b'CLIENTCHAL\x01', hashlib.sha1).digest()[:16]
    connection.sendall(framed + challenges[:8])
    test.assertEqual(frame()[4:], b'\xab\x83' + challenges[8:])
    keys, previous = b'', b''
    for i in range(1, 5):
        previous = hmac.new(prk, previous+b'BDDATA'+bytes([i]), hashlib.sha1).digest()
        keys += previous
    client_keys = keys[20:40]+keys[:20]+keys[56:72]+keys[40:56]
    test.assertEqual(codec.decode(frame()[4:], client_keys)[0], 4)
    sequence = 0

    def request(body):
        nonlocal sequence
        sequence += 1
        connection.sendall(codec.encode(0x86, body, client_keys, sequence))
        encrypted = frame()
        test.assertLessEqual(len(encrypted), 65536)
        kind, reply = codec.decode(encrypted[4:], client_keys)
        test.assertEqual(kind, 1)
        return reply

    return request
