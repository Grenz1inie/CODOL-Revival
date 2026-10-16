"""One Seatown match per game launch, triggered by this instance's Ready event."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .lifecycle import Services, alive, lobby_event
from .preparation import digest

NATIVE_HASHES = {
    'match-host/mainframe-verification/collision319.exe': 'e57ca57182ab677dffaa979ca2151849ae4f9938adc9960b09f890387d1f5b4a',
    'match-host/mainframe-verification/snapshot319_live.exe': 'd91ccd7f02fb7fd5e92bd95746972bd67d192cb32b49bb55e6a5366f79900167',
    'match-host/mainframe-verification/test_native_ncs319.exe': 'e432c4be23ea0e4675ff3550cf0e0ac0230cb5b96d5f18232de3244ebf987797',
}
INITIAL = 'match-host/activation-analysis319/initial-snapshot-living-loadout78-arms4-hands5-wf80-v2047-floor.bin'
ASSETS = (*NATIVE_HASHES, INITIAL, 'match-host/collision319/config319-27572-clipmap.bin',
          'match-host/collision319/ladders-mp_seatown.json', 'match-host/weapons319.txt',
          'match-host/playerdata_classes319.json', 'match-host/server-commands319.txt',
          'match-host/viewmodel-arms56.txt', 'match-host/mainframe-verification/config-reader-relocated.bin',
          'iips-memory/codoMP_client_shipRetail.exe.9076736.bin', 'weapon-parts319.txt', 'item-ids319.txt',
          'rankTable319.csv')


class MatchSession:
    def __init__(self, runtime, game, since, *, port=28970):
        self.runtime, self.game, self.since, self.port = Path(runtime), game, since, port
        self.assets = self.runtime / 'server'
        self.marker = self.assets / 'match-host/arm-loopback319.txt'
        self.phase, self.error = 'waiting', ''
        self.services = None
        self.run = None
        self.result = None

    def snapshot(self):
        return {'phase': self.phase, 'error': self.error, 'run': str(self.run) if self.run else None,
                'service': self.services.records[0] if self.services and self.services.records else None,
                'result': self.result}

    def poll(self):
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
        for name in ASSETS:
            if not (self.assets / name).is_file():
                raise FileNotFoundError(f'缺少 3.19 对局组件：{name}')
        for name, expected in NATIVE_HASHES.items():
            if digest(self.assets / name) != expected:
                raise ValueError(f'对局组件指纹不匹配：{name}')
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
        shutil.copy2(self.assets / INITIAL, snapshot)
        script = Path(__file__).resolve().parents[1] / 'server/match_host/diag_host319.py'
        python = Path(sys.executable)
        if python.name.lower() == 'pythonw.exe':
            python = python.with_name('python.exe')
        command = [str(python), '-B', '-I', '-X', 'utf8', str(script), '--port', str(self.port),
                   '--map', 'mp_seatown', '--gametype', 'tdm', '--seconds', '600', '--logdir', str(self.run),
                   '--stop-file', str(self.run / 'stop.request'), '--sequenced-probe', '3',
                   '--gamestate-probe-capture', str(self.runtime / 'game' / f"config319-{self.game['pid']}-first-netchan.txt"),
                   '--snapshot-probe-payload', str(snapshot), '--weapon', '187', '--viewmodels', '4', '5',
                   '--weapflags', '128', '--collision-map', str(self.assets / 'match-host/collision319/config319-27572-clipmap.bin'),
                   '--live-sim-seconds', '500', '--ack-client-commands', '--delta-continuation']
        self.services = Services(self.run, [{'name': 'match', 'port': self.port, 'protocol': 'UDP', 'command': command}],
                                 {**os.environ, 'CODOL319_SERVER_ROOT': str(self.assets), 'PYTHONUTF8': '1'})
        self.services.start()
        if not alive(self.game):
            raise RuntimeError('游戏已退出，对局未启动')
        self.marker.write_text(str(self.game['pid']), encoding='ascii')
        self.phase = 'running'

    def close(self):
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
