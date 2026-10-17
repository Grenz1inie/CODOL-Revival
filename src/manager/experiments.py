"""Stop support for repo-launched game sessions outside the manager runtime.

The fixed A-drive Ready-gate experiment (AGENTS.md, 2026-10-17) is the only
one today: its supervisor closes the game and services cleanly on
stop.request, so the manager routes there instead of killing processes. The
path is deliberately fixed; this is not a general process-management surface.
"""
import json
import subprocess
import time
from pathlib import Path

LAB = Path('A:/CODOL-Lab/ready319-20261017')


def _alive(pid):
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/FO', 'CSV', '/NH'],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=10, check=True)
    return f'"{pid}"' in result.stdout.decode('utf-8', 'replace')


def running(lab=LAB):
    try:
        state = json.loads((lab / 'startup.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return False
    return _alive((state.get('supervisor') or {}).get('pid'))


def stop(timeout=30.0, lab=LAB):
    """Signal a running lab session to stop and wait for its supervisor.

    Returns True when a session was running and reached a full stop, False
    when there was nothing to stop or it did not shut down in time.
    """
    if not running(lab):
        return False
    (lab / 'stop.request').touch()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not running(lab):
            return True
        time.sleep(0.2)
    return not running(lab)
