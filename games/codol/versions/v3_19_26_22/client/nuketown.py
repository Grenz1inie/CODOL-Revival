"""3.19 Rust map loading, using the admitted room and this process's resources."""
import json
from pathlib import Path
import sys
import time

from .lifecycle import Services, alive
from . import nuketown_assets

ROOT = Path(__file__).resolve().parents[5]
HOST = Path(__file__).resolve().parents[1] / 'server/match_host'
EXECUTABLE = ROOT / 'runtime/builds/codol/v3_19_26_22/rust-match/release/codol-match319.exe'


def request(runtime, since):
    path = Path(runtime) / 'server/nuketown-ready.json'
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding='utf-8'))
    return value if value['time'] >= since else None


class NuketownSession:
    def __init__(self, runtime, game, port):
        self.runtime, self.game, self.port = Path(runtime), game, port
        self.marker = self.runtime / 'server/match-host/arm-loopback319.txt'
        self.phase, self.error, self.run, self.services = 'waiting', '', None, None

    def start(self, room):
        self.marker.write_text('0', encoding='ascii')
        self.run = self.runtime / 'matches' / str(time.time_ns())
        self.run.mkdir(parents=True)
        spawn = nuketown_assets.build(self.runtime/'game', self.runtime/'generated/nuketown319',
                                     self.runtime/'server/match-host/ifs-read.exe')
        config = self.run / 'room.json'
        config.write_text(json.dumps({**room, 'port': self.port,
            'stop_file': str(self.run / 'stop.request'), 'gamestate_file': str(self.run / 'gamestate.bin'),
            'spawn_file': str(spawn)}), encoding='utf-8')
        self.services = Services(self.run, [{'name': 'match', 'protocol': 'UDP', 'port': self.port,
            'command': [str(EXECUTABLE), 'serve', str(config)]}])
        self.services.start()
        if not alive(self.game):
            raise RuntimeError('游戏已退出，对局未启动')
        self.marker.write_text(str(self.game['pid']), encoding='ascii')
        self.phase = 'running'

    def snapshot(self):
        return {'phase': self.phase, 'error': self.error, 'map': 'mp_nuked', 'gametype': 'cha',
            'run': str(self.run) if self.run else None,
            'service': self.services.records[0] if self.services and self.services.records else None,
            'result': None}

    def poll(self):
        if not alive(self.game):
            self.close()
        elif self.phase == 'running':
            if self.services.processes[0].poll() is not None:
                raise RuntimeError(f'Rust对局服务已退出，见 {self.run}')
            if not (self.run / 'gamestate.bin').exists():
                # Existing version-specific builder; incomplete captures return None.
                sys.path.insert(0, str(HOST))
                try:
                    from gamestate_probe319 import build_probe
                    capture = self.runtime / 'game' / f"config319-{self.game['pid']}-first-netchan.txt"
                    result = build_probe(capture, map_name='mp_nuked', game_type='cha', output_dir=self.run)
                finally:
                    sys.path.remove(str(HOST))
                if result:
                    temporary = self.run / 'gamestate.tmp'
                    temporary.write_bytes(result[0])
                    temporary.replace(self.run / 'gamestate.bin')
        return self.snapshot()

    def close(self):
        self.marker.write_text('0', encoding='ascii')
        if self.services:
            (self.run / 'stop.request').touch()
            self.services.close()
        if self.phase != 'error':
            self.phase = 'finished'
