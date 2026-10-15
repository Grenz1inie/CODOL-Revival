"""Extract explicitly named character streams from private marketplace IFS copies."""
import argparse
import json
from pathlib import Path
import re
import runpy
import shutil
import subprocess

from extract_story_resources import ROOT, GAME, DLL_SHA256, digest


def main(names):
    if not names or any(not re.fullmatch(r'[a-z0-9_]+', name) for name in names):
        raise ValueError('provide exact model stream basenames')
    stage = ROOT / 'research/experiments/story-native'
    dll = GAME / 'IIPS/IFS2.dll'
    if digest(dll) != DLL_SHA256:
        raise ValueError('IFS reader identity changed')
    reader = stage / 'ifs-read-models.exe'
    decode = runpy.run_path(str(ROOT/'research/references/codol2697/decode_loose_resources.py.txt'))['decode']
    requested = {'main/models/'+name for name in names}
    found = {name: [] for name in requested}
    for source in sorted((GAME/'IIPS/IIPSDownload').glob('lf_init_common_marketplace*.ifs')):
        folder = stage/'resources-character-streams'/source.stem
        folder.mkdir(parents=True, exist_ok=True)
        copy = folder/source.name
        source_hash = digest(source)
        if not copy.exists():
            shutil.copyfile(source, copy)
        if digest(copy) != source_hash:
            raise ValueError('IFS private copy differs from source')
        listing = folder/'directory.json'
        if not listing.exists():
            task = subprocess.run([str(reader), str(dll), str(copy), '--list', 'main\\models\\'],
                                  check=True, capture_output=True, text=True, timeout=60)
            listing.write_text(json.dumps([line.split('\t', 2) for line in task.stdout.splitlines()]))
        entries = json.loads(listing.read_text())
        for index, _, name in entries:
            key = name.lower().replace('\\', '/')
            if key not in requested:
                continue
            output = folder/index
            output.mkdir(exist_ok=True)
            if not (output/f'{index}.bin').exists():
                subprocess.run([str(reader), str(dll), str(copy), str(output), name],
                               check=True, capture_output=True, timeout=60)
            original_names = {}
            for entry, _, path in entries:
                if path.lower().endswith('.lst'):
                    for line in (output/f'{entry}.bin').read_text(encoding='utf-8-sig').splitlines():
                        original_names[line.lower().replace('\\', '/')] = line.replace('\\', '/').split('/')[-1]
            data = decode((output/f'{index}.bin').read_bytes(), original_names[key])
            decoded = output/'model.decoded'
            decoded.write_bytes(data)
            found[key].append(dict(archive=source.name, archive_sha256=source_hash,
                                  file=decoded.relative_to(ROOT).as_posix(), sha256=digest(decoded)))
        if digest(source) != source_hash or digest(copy) != source_hash:
            raise ValueError('archive changed during extraction')
    for name, variants in found.items():
        if not variants or len({row['sha256'] for row in variants}) != 1:
            raise ValueError(f'missing or conflicting stream: {name}')
        target = stage/'startup-assets'/name
        if target.exists() and digest(target) != variants[0]['sha256']:
            raise ValueError(f'existing stream differs: {name}')
        shutil.copyfile(ROOT/variants[0]['file'], target)
    manifest = stage/'resources-character-streams/installed.json'
    previous = json.loads(manifest.read_text()) if manifest.exists() else {}
    manifest.write_text(json.dumps(previous | found, indent=2))
    print(json.dumps(found, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('names', nargs='+')
    main(parser.parse_args().names)
