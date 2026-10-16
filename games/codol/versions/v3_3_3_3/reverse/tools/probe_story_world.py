"""Offline first-map dependency/world probe; does not start engine or network."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from story_engine_patch import patch_archive427
from decode_story_fastfile import CLIENT_SHA256

ROOT = Path(__file__).resolve().parents[6]
STAGE = ROOT / 'research/experiments/story-native'


def main():
    original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
    executable = STAGE / 'dedrun-3333-archive427.exe'
    executable.write_bytes(patch_archive427(original))
    client = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
    if hashlib.sha256(client.read_bytes()).hexdigest() != CLIENT_SHA256:
        raise ValueError('Current client hash mismatch')
    archives = [STAGE / name for name in (
        'resources-common-gfx/2.bin', 'resources-common-gfx/5.bin',
        'resources-common/ff_init_common_mp_V43/5.bin',
        'resources-base/ff_init_mp_cargoship_V32/2.bin',
        'resources/ff_init_coop_training_mp_cargoship_V29/2.bin')]
    command = [str(executable), '--codol-runtime-probe', str(client), 'mp_cargoship', *map(str, archives)]
    env = {k: v for k, v in os.environ.items() if not k.startswith('CODOL_')}
    env['CODOL_ARCHIVE_TRACE'] = '1'
    task = subprocess.run(command, cwd=STAGE, env=env, capture_output=True, text=True,
                          errors='backslashreplace', timeout=45, creationflags=subprocess.CREATE_NO_WINDOW)
    log = STAGE / 'runtime-world423.log'
    log.write_text(task.stdout + task.stderr, encoding='utf-8')
    (STAGE / 'runtime-world423.json').write_text(json.dumps({
        'command': command, 'returncode': task.returncode,
        'executable_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
        'inputs': [{'file': p.relative_to(ROOT).as_posix(),
                    'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in archives],
        'log': log.relative_to(ROOT).as_posix()}, indent=2), encoding='utf-8')
    print(task.stdout)
    print(task.stderr)
    return task.returncode


if __name__ == '__main__':
    raise SystemExit(main())
