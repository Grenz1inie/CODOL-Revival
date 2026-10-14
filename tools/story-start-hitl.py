"""Capture one manual story start and assert its visible outcome (diagnostic only)."""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
log = ROOT / 'runtime/logs/server.jsonl'
offset = log.stat().st_size
started = datetime.now(timezone.utc).isoformat()
print('Select Identity Unknown and click Start Match once. After 30 seconds report:', flush=True)
print('playable = map loaded and movement works; waiting = still Battle Start; error = error dialog; unresponsive = click has no effect', flush=True)
outcome = input().strip()
if outcome not in {'playable', 'waiting', 'error', 'unresponsive'}:
    raise SystemExit('Invalid observation; no verdict recorded')
with log.open('rb') as stream:
    stream.seek(offset)
    events = [json.loads(line) for line in stream if line.strip()]
result = {'started_utc': started, 'outcome': outcome,
          'observation_source': 'user', 'events': events}
path = ROOT / 'research/evidence' / ('story-start-hitl-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.json')
path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'{"PASS" if outcome == "playable" else "FAIL"}: {outcome}; evidence={path}', flush=True)
sys.exit(0 if outcome == 'playable' else 1)
