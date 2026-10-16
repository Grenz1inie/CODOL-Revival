"""Wrap already captured 3.19 mapped sections for static analysis only; not a runnable game."""
import hashlib
import json
from pathlib import Path
import struct

repo = Path(__file__).resolve().parents[2]
game = repo / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game'
original = game / 'codoMP_client_shipRetail.exe'
out = Path(__file__).resolve().parent
header = bytearray(original.read_bytes()[:4096])
pe = struct.unpack_from('<I', header, 0x3c)[0]
opt = pe + 24
sections = opt + struct.unpack_from('<H', header, pe + 20)[0]
struct.pack_into('<H', header, pe + 6, 3)
struct.pack_into('<I', header, opt + 16, 0x7f6330 - 0x400000)
header[opt + 96:opt + 224] = bytes(128)
header[sections:sections + 7 * 40] = bytes(7 * 40)
payload = bytearray()
sources = []
for index, (name, address, size, flags, suffix) in enumerate([
    (b'.text', 0x1000, 9072640, 0x60000020, 'text-00401000'),
    (b'.rdata', 0x8a8000, 1499136, 0x40000040, 'rdata-00ca8000'),
    (b'.data', 0xa16000, 230366400, 0xc0000080, None),
]):
    blob = b'' if suffix is None else (game / f'code319-44184-stage6-{suffix}.bin').read_bytes()
    struct.pack_into('<8sIIIIIIHHI', header, sections + index * 40,
                     name, size, address, len(blob), 4096 + len(payload) if blob else 0, 0, 0, 0, 0, flags)
    if suffix:
        sources.append({'file': f'code319-44184-stage6-{suffix}.bin', 'va': hex(address + 0x400000),
                        'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()})
    payload.extend(blob)
target = out / 'analysis-client319.exe'
target.write_bytes(header + payload)
metadata = {'version': '3.19.26.22', 'original_sha256': hashlib.sha256(original.read_bytes()).hexdigest(),
            'analysis_sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'image_base': '0x400000',
            'source': 'Saved isolated runtime stage6 snapshots, PID 44184; reused, no new capture',
            'coverage': sources, 'limitations': 'Synthesized PE header; data/BSS absent; runtime patches may exist; not executable; no UI proof'}
(out / 'analysis-image.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print(json.dumps(metadata))
