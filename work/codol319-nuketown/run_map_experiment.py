"""Attach the Rust map service to the already authorized A-drive test session."""
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path('A:/CODOL-Lab/ready319-20261017')
sys.path.insert(0, str(ROOT))
from games.codol.versions.v3_19_26_22.client.nuketown import NuketownSession, request
from games.codol.versions.v3_19_26_22.client.lifecycle import alive


def main():
    state = json.loads((EXPERIMENT / 'startup.json').read_text())
    gate = json.loads((EXPERIMENT / 'ready-gate-installed.json').read_text())
    game = state['game']
    if gate['pid'] != game['pid'] or not alive(game):
        raise ValueError('The verified experimental game is no longer running')
    session = NuketownSession(EXPERIMENT, game, 28970)
    output = EXPERIMENT / 'nuketown-experiment.json'
    try:
        output.write_text(json.dumps({'phase': 'waiting', 'game': game}))
        while alive(game) and not (EXPERIMENT / 'stop.request').exists():
            room = request(EXPERIMENT, game['created'])
            if room is not None:
                session.start(room)
                break
            time.sleep(.25)
        if session.run is None:
            return
        previous = None
        while alive(game) and not (EXPERIMENT / 'stop.request').exists() and not (session.run / 'stop.request').exists():
            status = session.poll()
            if status != previous:
                output.write_text(json.dumps(status, indent=2))
                previous = status
            time.sleep(.25)
    except BaseException:
        (EXPERIMENT / 'nuketown-experiment-error.txt').write_text(traceback.format_exc())
        raise
    finally:
        session.close()
        output.write_text(json.dumps(session.snapshot(), indent=2))


if __name__ == '__main__':
    main()
