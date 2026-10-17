"""Reproduce/verify the tracked 3.19 wire definitions from the original EXE.

Usage: python export_snapshot_fields319.py <original-exe> [--output <json>]
Without --output this verifies all tables and leaves the checkout unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

import pefile


DEFINITION = Path(__file__).resolve().parents[2] / 'server/match_host/snapshot_fields319.json'


def extract(executable):
    definition = json.loads(DEFINITION.read_text())
    data = Path(executable).read_bytes()
    if hashlib.sha256(data).hexdigest() != definition['source']['client_sha256']:
        raise ValueError('Expected the original 3.19.26.22 client EXE')
    with pefile.PE(data=data) as pe:
        for name, address in definition['source']['addresses'].items():
            rva = int(address, 16) - pe.OPTIONAL_HEADER.ImageBase
            if name == 'event_widths':
                definition[name] = list(struct.unpack('<185I', pe.get_data(rva, 185 * 4)))
            else:
                count = 246 if name == 'player' else 87 if name == 'client' else 63
                table = [list(struct.unpack('<Iii', pe.get_data(rva + index * 12, 12))) for index in range(count)]
                if name.startswith('entity_'):
                    definition['entity'][int(name.split('_')[1])] = table
                else:
                    definition[name] = table
    return definition


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = extract(args.executable)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    elif result != json.loads(DEFINITION.read_text()):
        raise SystemExit('Tracked snapshot fields differ from the original EXE')
    print('Verified 27 original 3.19 wire tables')
