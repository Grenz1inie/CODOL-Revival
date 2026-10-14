"""Export first-map/base-map rawfiles and registries for reverse engineering."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

from decode_story_fastfile import decode
from index_story_zone import read_assets, read_ncs, read_rawfile, read_baselines

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'research/experiments/story-native'


def main():
    client = (ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe').read_bytes()
    destination = STAGE / 'zone-assets'
    destination.mkdir(exist_ok=True)
    report = []
    sources = ['resources', 'resources-base']
    if (STAGE / 'resources-common/manifest.json').exists():
        sources.append('resources-common')
    for source in sources:
        manifest = json.loads((STAGE / source / 'manifest.json').read_text())
        for archive in manifest['archives']:
            for item in archive['files']:
                if not item['name'].endswith('.ff'):
                    continue
                name = Path(item['name']).stem
                zone = decode(client, (ROOT / item['file']).read_bytes(), name)
                assets = read_assets(zone)
                folder = destination / name
                folder.mkdir(exist_ok=True)
                (folder / 'zone.bin').write_bytes(zone)
                row = {'name': name, 'assets': len(assets), 'kinds': dict(Counter(k for k, _ in assets)),
                       'zone_sha256': hashlib.sha256(zone).hexdigest(), 'ncs': [], 'rawfiles': [], 'entities': [], 'baselines': []}
                for index, (kind, data) in enumerate(assets):
                    if kind == 44:
                        try:
                            row['ncs'].append(read_ncs(data))
                        except ValueError as error:
                            # Common tables may reference load-block strings; retain
                            # unresolved evidence instead of inventing an ID mapping.
                            row['ncs'].append({'asset_index': index, 'status': 'unresolved', 'reason': str(error)})
                    if kind == 36:
                        name_ptr, packed, size, _ = struct.unpack_from('<4I', data)
                        if name_ptr != 0xffffffff and packed == size == 0:
                            row['rawfiles'].append({'name': None, 'name_reference': hex(name_ptr), 'bytes': 0})
                            continue
                        filename, payload = read_rawfile(data)
                        output = folder / f'{index}.raw'
                        output.write_bytes(payload)
                        row['rawfiles'].append({'name': filename, 'file': output.relative_to(ROOT).as_posix(),
                                                'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()})
                        if filename.lower().startswith('mp/constbaselines/') and filename.endswith('.bin'):
                            rows = read_baselines(payload)
                            row['baselines'].append({'name': filename, 'file': output.relative_to(ROOT).as_posix(),
                                                     'count': len(rows), 'stride': 272,
                                                     'entries': [{k: v for k, v in record.items() if k != 'state'} for record in rows]})
                    if kind == 42:
                        end = data.index(b'\0', 52)
                        filename = data[52:end].decode('ascii')
                        size = struct.unpack_from('<I', data, 8)[0]
                        payload = data[end + 1:end + 1 + size]
                        if len(payload) != size:
                            raise ValueError('truncated entity text')
                        output = folder / f'{index}.mapents'
                        output.write_bytes(payload)
                        row['entities'].append({'name': filename, 'file': output.relative_to(ROOT).as_posix(), 'bytes': size})
                (folder / 'index.json').write_text(json.dumps(row, indent=2), encoding='utf-8')
                report.append(row)
                (destination / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
                print(name, len(zone), len(assets), row['kinds'])


if __name__ == '__main__':
    main()
