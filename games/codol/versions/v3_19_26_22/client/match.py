"""One Seatown match per game launch, triggered by this instance's Ready event."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .lifecycle import Services, alive, lobby_event
from .preparation import CLIENT
from . import native_build
from .resource_export import validate_common
from ..server.match_host.snapshot_codec319 import encode
from . import nuketown

def initial_snapshot():
    # Reproduces the historical Seatown floor baseline byte for byte.
    return encode('100000 100000 1370 -384 233.908 0 0 0 0 180 0 2046', 78, (4, 5), 128)


class MatchSession:
    def __init__(self, runtime, game, since, *, port=28970):
        self.runtime, self.game, self.since, self.port = Path(runtime), game, since, port
        self.assets = self.runtime / 'server'
        self.marker = self.assets / 'match-host/arm-loopback319.txt'
        self.phase, self.error = 'waiting', ''
        self.services = None
        self.run = None
        self.result = None
        self.nuketown = None

    def snapshot(self):
        if self.nuketown:
            return self.nuketown.snapshot()
        return {'phase': self.phase, 'error': self.error, 'run': str(self.run) if self.run else None,
                'service': self.services.records[0] if self.services and self.services.records else None,
                'result': self.result}

    def poll(self):
        room = nuketown.request(self.runtime, self.since) if self.phase == 'waiting' and not self.nuketown else None
        if self.nuketown or (room and alive(self.game)):
            try:
                if self.nuketown is None:
                    self.nuketown = nuketown.NuketownSession(self.runtime, self.game, self.port)
                    self.nuketown.start(room)
                return self.nuketown.poll()
            except Exception as error:
                self.nuketown.phase, self.nuketown.error = 'error', str(error)
                self.nuketown.close()
                return self.nuketown.snapshot()
        if not alive(self.game):
            self.close()
        elif self.phase == 'waiting' and lobby_event(self.assets / 'lsg-handshake.jsonl', 'room_ready', self.since):
            try:
                self.start()
            except Exception as error:
                self.phase, self.error = 'error', str(error)
                self.close()
        elif self.phase == 'running' and self.services.processes[0].poll() is not None:
            code = self.services.processes[0].returncode
            if code:
                self.phase, self.error = 'error', f'对局服务退出，代码 {code}，见 {self.run}'
            self.close()
        return self.snapshot()

    def start(self):
        self.marker.write_text('0', encoding='ascii')
        native_build.validate(self.assets / 'match-host')
        validate_common(self.assets)
        self.run = self.runtime / 'matches' / str(time.time_ns())
        self.run.mkdir(parents=True)
        # Preserve existing progress before this match can award XP or currency.
        for name in ('profile319.json', 'local-profiles319/wallet.json'):
            source = self.assets / name
            if source.exists():
                target = self.run / 'backups' / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
        snapshot = self.run / 'initial-snapshot.bin'
        snapshot.write_bytes(initial_snapshot())
        script = Path(__file__).resolve().parents[1] / 'server/match_host/diag_host319.py'
        python = Path(sys.executable)
        if python.name.lower() == 'pythonw.exe':
            python = python.with_name('python.exe')
        command = [str(python), '-B', '-I', '-X', 'utf8', str(script), '--port', str(self.port),
                   '--map', 'mp_seatown', '--gametype', 'tdm', '--seconds', '600', '--logdir', str(self.run),
                   '--stop-file', str(self.run / 'stop.request'), '--sequenced-probe', '3',
                   '--gamestate-probe-capture', str(self.runtime / 'game' / f"config319-{self.game['pid']}-first-netchan.txt"),
                   '--snapshot-probe-payload', str(snapshot), '--weapon', '187', '--viewmodels', '4', '5',
                   '--weapflags', '128', '--collision-map', str(self.run / 'clipmap.bin'),
                   '--resource-game', str(self.game['pid']), str(self.game['created']), str(self.runtime / 'game' / CLIENT),
                   '--live-sim-seconds', '500', '--ack-client-commands', '--delta-continuation']
        self.services = Services(self.run, [{'name': 'match', 'port': self.port, 'protocol': 'UDP', 'command': command}],
                                 {**os.environ, 'CODOL319_SERVER_ROOT': str(self.assets), 'PYTHONUTF8': '1'})
        self.services.start()
        if not alive(self.game):
            raise RuntimeError('游戏已退出，对局未启动')
        self.marker.write_text(str(self.game['pid']), encoding='ascii')
        self.phase = 'running'

    def close(self):
        if self.nuketown:
            self.nuketown.close()
            return
        if self.marker.parent.exists():
            self.marker.write_text('0', encoding='ascii')
        if self.services:
            if self.services.processes and self.services.processes[0].poll() is None:
                (self.run / 'stop.request').touch()
                try:
                    self.services.processes[0].wait(timeout=8)
                except subprocess.TimeoutExpired:
                    self.phase, self.error = 'error', f'对局停止超时，结算未确认，见 {self.run}'
            self.services.close()
            log = self.run / 'diag-host319.jsonl'
            if log.exists():
                with log.open(encoding='utf-8') as stream:
                    for line in stream:
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if event.get('event') in ('match_pay', 'match_pay_failed'):
                            self.result = event
        if self.phase != 'error':
            self.phase = 'finished'
