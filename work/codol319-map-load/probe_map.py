"""Bounded read-only map-entity capture from the authorized A-drive experiment."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from games.codol.versions.v3_19_26_22.client.resource_export import ReadOnlyProcess
from games.codol.versions.v3_19_26_22.client.loaded_resources import LoadedResources

OUT = Path(__file__).resolve().parent
LAB = Path('A:/CODOL-Lab/ready319-20261017')


def main():
    game = json.loads((LAB/'startup.json').read_text())['game']
    executable = LAB/'game/codoMP_client_shipRetail.exe'
    reference = (ROOT/'work/codol319-console/analysis-client319.exe').read_bytes()
    with ReadOnlyProcess(game, executable) as process:
        # Static VAs are valid only at this image base. Follow loaded pointers verbatim.
        address = 0x617045
        if process.read(address, 19) != reference[address-0x400000:address-0x400000+19]:
            raise ValueError('Map-entity consumer bytes or image base differ')
        loaded = LoadedResources(process.read)
        entries = process.read(0x239b120, 150000*28)
        heads = struct.unpack('<120000I', process.read(0x1e2d338, 120000*4))
        seen, maps = set(), []
        for index in heads:
            while index and index not in seen:
                if index >= 150000: raise ValueError('Invalid asset chain')
                seen.add(index)
                row = struct.unpack_from('<7I', entries, index*28)
                if row[0] in (15, 16, 17, 42):
                    try:
                        name = loaded.string(loaded.words(row[2])[0])
                        maps.append({'kind': row[0], 'address': hex(row[2]), 'name': name})
                    except (ValueError, OSError):
                        pass
                index = row[5]
        (OUT/'loaded-maps.json').write_text(json.dumps({'game': game, 'assets': maps}, indent=2))
        clip_address = loaded.asset(15, 'maps/mp/mp_nuked.d3dbsp')
        clip = process.read(clip_address, 256)
        clip_name = process.read(struct.unpack_from('<I', clip)[0], 64).split(b'\0')[0]
        if clip_name != b'maps/mp/mp_nuked.d3dbsp':
            raise ValueError(f'Unexpected loaded clipmap: {clip_name!r}')
        entity_address = struct.unpack_from('<I', clip, 0x98)[0]
        header = process.read(entity_address, 64)
        text_address, length = struct.unpack_from('<II', header, 4)
        if not 1 <= length <= 4*1024*1024:
            raise ValueError(f'Entity text length not bounded: {length}')
        data = process.read(text_address, length)
        (OUT/'mapents.bin').write_bytes(data)
        result = {'version': '3.19.26.22', 'game': game,
                  'exe_sha256': hashlib.sha256(executable.read_bytes()).hexdigest(),
                  'consumer_va': hex(address), 'clipmap_runtime_pointer': hex(clip_address),
                  'mapents_runtime_pointer': hex(entity_address),
                  'text_runtime_pointer': hex(text_address), 'header_hex': header.hex(),
                  'bytes': length, 'sha256': hashlib.sha256(data).hexdigest(),
                  'source': 'ReadProcessMemory 0x410; fixed experimental path and process creation time',
                  'coverage': 'Loaded mp_nuked entity text; static consumer byte check',
                  'unverified': 'REA cross-check pending; spawn selection and actual gameplay'}
        (OUT/'mapents.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(result))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        (OUT/'probe-error.txt').write_text(traceback.format_exc())
        raise
