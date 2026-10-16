"""Decode extracted loose assets and check first-map .lst coverage, per package.

Uses the retained reference decoder (format attribution in that source); it does
not run its main(), overlay patch packages, or interpret FF content as scripts.
"""
import hashlib
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[6]
STAGE = ROOT / 'research/experiments/story-native/resources'


def main():
    manifest = json.loads((STAGE / 'manifest.json').read_text())
    decode = runpy.run_path(str(ROOT / 'research/references/codol2697/decode_loose_resources.py.txt'))['decode']
    names = {}
    for archive in manifest['archives']:
        for item in archive['files']:
            if item['name'].endswith('.lst'):
                for name in (ROOT / item['file']).read_text(encoding='utf-8-sig').splitlines():
                    name = name.replace('\\', '/')
                    names[name.lower()] = name
    present = {item['name'].lower() for a in manifest['archives'] for item in a['files']}
    report = {'map': manifest['map'], 'listed_unique': len(names), 'present_unique': len(present),
              'missing_listed': sorted(set(names) - present), 'files': [], 'failures': []}
    for archive in manifest['archives']:
        for item in archive['files']:
            name = item['name']
            if name.endswith(('.ff', '.lst')):
                continue
            source = ROOT / item['file']
            try:
                data = decode(source.read_bytes(), names[name.lower()].split('/')[-1])
                if name.endswith('.iwi') and not data.startswith(b'IWi\x09'):
                    raise ValueError('unexpected texture header')
                output = source.with_suffix('.decoded')
                with output.open('xb') as stream:
                    stream.write(data)
                report['files'].append({'archive': archive['archive'], 'name': name,
                                        'file': output.relative_to(ROOT).as_posix(), 'size': len(data),
                                        'sha256': hashlib.sha256(data).hexdigest(), 'header': data[:16].hex()})
            except (ValueError, KeyError) as error:
                report['failures'].append({'archive': archive['archive'], 'name': name, 'error': str(error)})
    (STAGE / 'inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in report.items() if key != 'files'}, indent=2))
    print('decoded', len(report['files']))


if __name__ == '__main__':
    main()
