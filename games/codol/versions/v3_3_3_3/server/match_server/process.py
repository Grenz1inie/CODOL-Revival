# SPDX-License-Identifier: AGPL-3.0-or-later
"""Own one native match process through its ready/reserve JSONL control pipe."""
import itertools
import json
import os
from pathlib import Path
import queue
import subprocess
import threading


ROOT = Path(__file__).resolve().parents[6]
RUNTIME = Path(os.environ.get('CODOL_RUNTIME', ROOT / 'runtime/instances/codol-3.3.3.3-offline'))
READY_TIMEOUT = 60.0
RESPONSE_TIMEOUT = 10.0
CLOSE_TIMEOUT = 3.0


class NativeMatchProcess:
    def __init__(self, directory, port=28970, record=None):
        if type(port) is not int or not 0 <= port <= 65535:
            raise ValueError('port must be between 0 and 65535')
        self.port, self.map_name, self.netconst_checksum = port, None, None
        self._record = record
        self._process = self._reader = self._stderr = None
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._close_lock = threading.Lock()
        self._ready = queue.Queue()
        self._pending = {}
        self._ids = itertools.count(1)
        self._failure = None
        self._closed = False
        try:
            log = Path(os.environ.get('CODOL_RUNTIME', RUNTIME)) / 'logs/match-rust.stderr.log'
            log.parent.mkdir(parents=True, exist_ok=True)
            self._stderr = log.open('ab', buffering=0)
            executable = ROOT / 'runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe'
            self._process = subprocess.Popen(
                [str(executable), 'serve', '--package', str(Path(directory).resolve()),
                 '--port', str(port)], cwd=ROOT, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=self._stderr, text=True,
                encoding='utf-8', bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            self._reader = threading.Thread(target=self._read,
                                            name='codol-match-control', daemon=True)
            self._reader.start()
            ready = self._wait(self._ready, READY_TIMEOUT, 'ready')
            self.port = ready['port']
            self.map_name = ready['map']
            self.netconst_checksum = ready['checksum']
            if not self.is_alive():
                raise RuntimeError('native match process exited during startup')
        except BaseException:
            self.close()
            raise

    @property
    def pid(self):
        return self._process.pid

    def is_alive(self):
        with self._lock:
            return (not self._closed and self._failure is None
                    and self._process is not None and self._process.poll() is None)

    @staticmethod
    def _wait(mailbox, timeout, operation):
        try:
            response = mailbox.get(timeout=timeout)
        except queue.Empty:
            raise TimeoutError(f'native match {operation} timed out') from None
        if isinstance(response, str):
            raise RuntimeError(response)
        return response

    def _fail(self, reason):
        with self._lock:
            if self._failure is not None:
                return
            self._failure = reason
            self._ready.put(reason)
            for mailbox in self._pending.values():
                mailbox.put(reason)

    def _event(self, message):
        if self._record is None:
            return

        def public(value):
            if isinstance(value, dict):
                return {k: public(v) for k, v in value.items() if k not in ('sid', 'key')}
            if isinstance(value, list):
                return [public(v) for v in value]
            return value

        fields = public({k: v for k, v in message.items() if k != 'event'})
        try:
            self._record(message['event'], **fields)
        except Exception:
            # A telemetry callback must not strand control responses behind it.
            pass

    def _read(self):
        ready_seen = False
        try:
            for line in self._process.stdout:
                message = json.loads(line)
                if not isinstance(message, dict) or not isinstance(message.get('event'), str):
                    raise ValueError('invalid control event')
                event = message['event']
                if event == 'ready':
                    if (ready_seen or type(message.get('port')) is not int
                            or not 1 <= message['port'] <= 65535
                            or not isinstance(message.get('map'), str) or not message['map']
                            or type(message.get('checksum')) is not int
                            or not 0 <= message['checksum'] < 1 << 32):
                        raise ValueError('invalid ready event')
                    ready_seen = True
                    self._ready.put(message)
                    continue
                if event in ('reserved', 'error'):
                    with self._lock:
                        request_id = message.get('id')
                        mailbox = self._pending.get(request_id) if type(request_id) is int else None
                        if mailbox is not None:
                            mailbox.put(message)
                    if event == 'reserved':
                        continue
                self._event(message)
        except (OSError, ValueError):
            # Never include raw lines or reservation material in errors/logs.
            self._fail('invalid or unreadable native match control stream')
        finally:
            self._fail('native match control stream closed')

    def reserve(self, owner, sidbytes8, keybytes16):
        """Return the acknowledged UDP port; no reservation is inferred locally."""
        if type(owner) is not int or not 0 < owner < 1 << 64:
            raise ValueError('reservation requires a valid owner')
        if not isinstance(sidbytes8, bytes) or len(sidbytes8) != 8:
            raise ValueError('security ID must contain 8 bytes')
        if not isinstance(keybytes16, bytes) or len(keybytes16) != 16:
            raise ValueError('security key must contain 16 bytes')
        mailbox = queue.Queue()
        with self._lock:
            if self._failure is not None or self._closed or self._process.poll() is not None:
                raise RuntimeError('native match process is not available')
            request_id = next(self._ids)
            self._pending[request_id] = mailbox
        try:
            request = dict(id=request_id, op='reserve', uid=owner,
                           sid=sidbytes8.hex(), key=keybytes16.hex())
            with self._write_lock:
                with self._lock:
                    if self._failure is not None or self._closed:
                        raise RuntimeError('native match process is not available')
                try:
                    self._process.stdin.write(json.dumps(request, separators=(',', ':')) + '\n')
                    self._process.stdin.flush()
                except (OSError, ValueError):
                    self._fail('native match control input closed')
                    raise RuntimeError('native match control input closed') from None
            response = self._wait(mailbox, RESPONSE_TIMEOUT, 'reservation')
            if response['event'] == 'error':
                raise RuntimeError('native match reservation rejected')
            if type(response.get('port')) is not int or response['port'] != self.port:
                raise RuntimeError('native match reservation port mismatch')
            return response['port']
        finally:
            with self._lock:
                self._pending.pop(request_id, None)

    def close(self):
        with self._close_lock:
            with self._lock:
                if self._closed:
                    return
                self._closed = True
            self._fail('native match process closed')
            child = self._process
            try:
                if child is not None:
                    # EOF is the native owner's shutdown signal. No global PID
                    # lookup or process-tree kill is used, including on failure.
                    with self._write_lock:
                        try:
                            child.stdin.close()
                        except (OSError, ValueError):
                            pass
                    try:
                        child.wait(timeout=CLOSE_TIMEOUT)
                    except subprocess.TimeoutExpired:
                        child.terminate()
                        try:
                            child.wait(timeout=CLOSE_TIMEOUT)
                        except subprocess.TimeoutExpired:
                            child.kill()
                            child.wait(timeout=CLOSE_TIMEOUT)
                    if self._reader is not None and self._reader is not threading.current_thread():
                        self._reader.join(timeout=CLOSE_TIMEOUT)
                    child.stdout.close()
            finally:
                if self._stderr is not None:
                    self._stderr.close()
