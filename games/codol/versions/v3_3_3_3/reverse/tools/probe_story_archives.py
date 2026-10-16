"""Run only the reference engine's offline archive entrypoint on isolated copies."""
import hashlib
import json
import os
from pathlib import Path
import subprocess

from story_engine_patch import patch_archive427

ROOT = Path(__file__).resolve().parents[6]
STAGE = ROOT / 'research/experiments/story-native'


def main():
    original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
    patched = patch_archive427(original)
    executable = STAGE / 'dedrun-3333-archive427.exe'
    executable.write_bytes(patched)
    client = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
    if hashlib.sha256(client.read_bytes()).hexdigest() != 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b':
        raise ValueError('Current client hash mismatch')
    env = {k: v for k, v in os.environ.items() if not k.startswith('CODOL_')}
    env['CODOL_ARCHIVE_TRACE'] = '1'
    rows = []
    for source in ('resources', 'resources-base'):
        manifest = json.loads((STAGE / source / 'manifest.json').read_text())
        for item in (f for a in manifest['archives'] for f in a['files'] if f['name'].endswith('.ff')):
            task = subprocess.run([str(executable), '--codol-archive-probe', str(ROOT / item['file']), str(client)],
                                  cwd=STAGE, env=env, capture_output=True, text=True,
                                  errors='backslashreplace', timeout=30,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            log = STAGE / (Path(item['name']).name + '.probe.log')
            log.write_text(task.stdout + task.stderr, encoding='utf-8')
            rows.append({'map': Path(item['name']).stem, 'returncode': task.returncode,
                         'log': log.relative_to(ROOT).as_posix()})
            print(rows[-1]['map'], task.returncode, task.stdout.splitlines()[:3])
    (STAGE / 'archive427-probes.json').write_text(json.dumps({
        'input_sha256': hashlib.sha256(original).hexdigest(),
        'output_sha256': hashlib.sha256(patched).hexdigest(),
        'input_size': len(original),
        'output_size': len(patched),
        'appended_bytes': len(patched) - len(original),
        'appended_sha256': hashlib.sha256(patched[len(original):]).hexdigest(),
        'changed_offsets': [hex(i) for i, (a, b) in enumerate(zip(original, patched)) if a != b],
        'probes': rows}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
