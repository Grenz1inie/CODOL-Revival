"""Stage current shared/first-map model streams for the isolated native engine."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile

from extract_story_resources import ROOT, GAME, DLL_SHA256, digest

STAGE = ROOT / 'research/experiments/story-native'


def main(pvp=False):
    dll = GAME / 'IIPS/IFS2.dll'
    if digest(dll) != DLL_SHA256:
        raise ValueError('IFS reader DLL identity changed')
    compiler = Path('A:/Coding/MinGW/bin')
    env = dict(os.environ, PATH=str(compiler)+os.pathsep+os.environ['SystemRoot']+'/System32')
    reader = STAGE / 'ifs-read-models.exe'
    subprocess.run([str(compiler/'gcc.exe'), '-O2', '-Wall', '-static-libgcc',
                    '-o', str(reader), str(ROOT/'games/codol/versions/v3_3_3_3/reverse/tools/ifs-read.c')], env=env, check=True)
    decode = runpy.run_path(str(ROOT/'research/references/codol2697/decode_loose_resources.py.txt'))['decode']
    if pvp:
        catalog = {'archives': []}
        downloads = GAME/'IIPS/IIPSDownload'
        sources = sorted({*downloads.glob('lf_init_common_gametype_mp*.ifs'),
                          *downloads.glob('lf_init_mp_killhouse_sh_*.ifs')})
        for source in sources:
            source_hash = digest(source)
            with tempfile.TemporaryDirectory(prefix='pvp-directory-', dir=STAGE) as temporary:
                copy = Path(temporary)/source.name
                shutil.copyfile(source, copy)
                result = subprocess.run([str(reader), str(dll), str(copy), '--list', 'main\\models\\'],
                                        capture_output=True, text=True, timeout=60, check=True)
                entries = [dict(name=line.split('\t', 2)[2]) for line in result.stdout.splitlines()]
                if digest(source) != source_hash or digest(copy) != source_hash:
                    raise ValueError('Archive changed during listing')
            catalog['archives'].append(dict(archive=source.name, sha256=source_hash, entries=entries))
    else:
        catalog = json.loads((ROOT/'research/evidence/story-common-loose-directory.json').read_text())
    output = STAGE / 'resources-models'
    output.mkdir(exist_ok=True)
    records = []
    for archive in catalog['archives']:
        if not any(e['name'].lower().replace('\\', '/').startswith('main/models/') for e in archive['entries']):
            continue
        source = GAME / 'IIPS/IIPSDownload' / archive['archive']
        if digest(source) != archive['sha256']:
            raise ValueError(f'Archive identity changed: {source.name}')
        folder = output / source.stem
        manifest = folder / 'manifest.json'
        if manifest.exists():
            rows = json.loads(manifest.read_text())
            if any(digest(ROOT/r['file']) != r['sha256'] for r in rows):
                raise ValueError(f'Cached model changed: {folder.name}')
        else:
            folder.mkdir(exist_ok=True)
            # The recovered DLL reads a private archive copy, never the game file.
            with tempfile.TemporaryDirectory(prefix='model-extract-', dir=STAGE) as temporary:
                temporary = Path(temporary)
                copy = temporary / source.name
                shutil.copyfile(source, copy)
                result = subprocess.run([str(reader), str(dll), str(copy), str(temporary), 'main\\models\\'],
                                        capture_output=True, text=True, timeout=60, check=True)
                entries = [line.split('\t', 2) for line in result.stdout.splitlines()]
                names = {}
                for index, _, name in entries:
                    if name.endswith('.lst'):
                        for line in (temporary/f'{index}.bin').read_text(encoding='utf-8-sig').splitlines():
                            names[line.lower().replace('\\', '/')] = line.replace('\\', '/').split('/')[-1]
                rows = []
                for index, _, name in entries:
                    key = name.lower().replace('\\', '/')
                    if not key.startswith('main/models/'):
                        continue
                    raw = (temporary/f'{index}.bin').read_bytes()
                    data = decode(raw, names[key])
                    target = folder / f'{index}.decoded'
                    target.write_bytes(data)
                    rows.append(dict(archive=source.name, archive_sha256=archive['sha256'], name=key,
                        file=target.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(data).hexdigest(),
                        encoded_sha256=hashlib.sha256(raw).hexdigest(), header=data[:8].hex()))
                if digest(source) != archive['sha256'] or digest(copy) != archive['sha256']:
                    raise ValueError('Archive changed during extraction')
            manifest.write_text(json.dumps(rows, indent=2))
        records.extend(rows)
    if not pvp:
        first = json.loads((STAGE/'resources/inspection.json').read_text())
        records.extend(r for r in first['files'] if r['name'].lower().replace('\\', '/').startswith('main/models/'))
    by_name = {}
    for row in records:
        by_name.setdefault(row['name'].lower().replace('\\', '/'), []).append(row)
    conflicts, installed = [], []
    for name, variants in by_name.items():
        if len({r['sha256'] for r in variants}) != 1:
            conflicts.append(dict(name=name, variants=variants))
            continue  # No unverified patch-precedence guess; retain both sources.
        path = Path(name)
        if len(path.parts) != 3 or path.parts[:2] != ('main', 'models') or path.name in ('.', '..'):
            raise ValueError(f'Unexpected model name: {name}')
        target = STAGE/'startup-assets'/path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists() and digest(target) != variants[0]['sha256']:
            raise ValueError(f'Staged model differs: {name}')
        shutil.copyfile(ROOT/variants[0]['file'], target)
        installed.append(dict(name=name, sha256=digest(target), sources=variants))
    report = dict(installed=installed, conflicts=conflicts, dll_sha256=DLL_SHA256,
                  reader_sha256=digest(reader), gameplay_verified=False)
    report_name = 'server3333-pvp-model-streams.json' if pvp else 'server3333-model-streams.json'
    (ROOT/'research/evidence'/report_name).write_text(json.dumps(report, indent=2))
    print(json.dumps(dict(installed=len(installed), conflicts=[r['name'] for r in conflicts])))


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pvp', action='store_true', help='stage shared MP and Killhouse models')
    main(parser.parse_args().pvp)
