"""Owned loopback processes; no cleanup by executable name or port alone."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time

import psutil


def identity(pid):
    return {'pid': pid, 'created': psutil.Process(pid).create_time()}


def alive(process):
    try:
        return psutil.Process(process['pid']).create_time() == process['created']
    except (psutil.NoSuchProcess, KeyError, TypeError):
        return False


def listeners():
    return {(c.laddr.port, c.pid) for c in psutil.net_connections(kind='tcp')
            if c.status == psutil.CONN_LISTEN and c.laddr.ip in ('127.0.0.1', '0.0.0.0', '::')}


def service_status(records):
    bound = listeners()
    ports = []
    running = False
    for record in records:
        owned = alive(record)
        running |= owned
        listening = owned and (record['port'], record['pid']) in bound
        ports.append({'name': record['name'], 'protocol': 'TCP', 'port': record['port'],
                      'listening': listening,
                      'conflict': any(port == record['port'] and pid != record['pid'] for port, pid in bound)})
    return {'running': running, 'ready': bool(ports) and all(p['listening'] for p in ports), 'ports': ports}


class Services:
    def __init__(self, runtime, specifications, env=None):
        self.runtime, self.specifications = Path(runtime), specifications
        self.env = env
        self.processes, self.records = [], []

    def start(self, timeout=10):
        # Check every port before starting anything; never kill another installation.
        for spec in self.specifications:
            with socket.socket() as sock:
                try:
                    sock.bind(('127.0.0.1', spec['port']))
                except OSError as error:
                    raise OSError(f"端口 {spec['port']} 已被占用，请先关闭占用程序") from error
        logs = self.runtime / 'logs'
        logs.mkdir(parents=True, exist_ok=True)
        try:
            for spec in self.specifications:
                with (logs / (spec['name'] + '.log')).open('ab') as out:
                    process = subprocess.Popen(spec['command'], cwd=self.runtime, env=self.env,
                        stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT, close_fds=True,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                self.processes.append(process)
                self.records.append({**identity(process.pid), 'name': spec['name'], 'port': spec['port']})
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                for spec, process in zip(self.specifications, self.processes):
                    if process.poll() is not None:
                        raise RuntimeError(f"{spec['name']} 启动失败，退出码 {process.returncode}，见 {logs}")
                if self.status()['ready']:
                    return
                time.sleep(0.05)
            raise TimeoutError(f'本地服务未就绪，见 {logs}')
        except BaseException:
            self.close()
            raise

    def status(self):
        return service_status(self.records)

    def close(self):
        for process in reversed(self.processes):
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)


def lobby_ready(log, since):
    try:
        lines = Path(log).read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return False
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:  # The service may be appending its last line.
            continue
        if event.get('event') == 'secure_profile_read' and event.get('time', 0) >= since:
            return True
    return False
