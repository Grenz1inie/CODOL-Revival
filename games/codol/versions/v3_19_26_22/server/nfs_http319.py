"""Local stand-in for the Tencent web services the 3.19 client fetches (configs_s
[tencent_config]/[tencent_nfs_config] url): logs every request to nfs-http319.jsonl and serves
files from nfs-www/ when they exist (404 otherwise). Loopback only.
Usage: nfs_http319.py [port]   (default 8319)"""
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os

H = Path(os.environ['CODOL319_SERVER_ROOT']) / 'match-host'
WWW = H / 'nfs-www'
LOG = H / 'nfs-http319.jsonl'


class Handler(BaseHTTPRequestHandler):
    def _serve(self, body=b''):
        path = self.path.split('?', 1)[0].lstrip('/')
        target = (WWW / path).resolve()
        if target.is_dir():
            target = target / 'index.json'          # /nfs/dev/ -> the advertisement list
        ok = WWW.resolve() in target.parents and target.is_file()
        data = target.read_bytes() if ok else b''
        with LOG.open('a', encoding='utf-8') as out:
            out.write(json.dumps(dict(time=time.time(), method=self.command, path=self.path,
                                      headers=dict(self.headers), body=body[:4096].hex(),
                                      served=len(data) if ok else None)) + '\n')
        self.send_response(200 if ok else 404)
        ctype = 'image/jpeg' if path.endswith('.jpg') else 'image/png' if path.endswith('.png') else 'application/json' if target.name.endswith('.json') else 'application/octet-stream'
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def do_GET(self):
        self._serve()

    def do_HEAD(self):
        self._serve()

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        self._serve(self.rfile.read(n) if n else b'')

    def log_message(self, *a):
        pass


if __name__ == '__main__':
    WWW.mkdir(exist_ok=True)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8319
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()
