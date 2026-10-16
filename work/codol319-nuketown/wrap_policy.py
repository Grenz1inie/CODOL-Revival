"""Small static-only PE with original inventory code/data pages and original VAs."""
from pathlib import Path
import hashlib
import json
import struct

root = Path(__file__).resolve().parent
source = (root.parent / 'codol319-console/analysis-client319.exe').read_bytes()
header = bytearray(source[:4096])
pe = struct.unpack_from('<I', header, 0x3c)[0]
opt = pe + 24
sections = opt + struct.unpack_from('<H', header, pe + 20)[0]
ranges = [(0x623000,0x1a000,0x60000020),(0x760000,0x20000,0x60000020),(0x7e7000,0x10000,0x60000020),(0x806000,0x4000,0x60000020),(0xb75000,0x2b000,0x60000020),(0xca8000,0x16e000,0x40000040)]
struct.pack_into('<H', header, pe + 6, len(ranges))
struct.pack_into('<I', header, opt + 16, 0x62feb0 - 0x400000)
struct.pack_into('<I', header, opt + 56, 0xa16000)
header[sections:sections + 16 * 40] = bytes(16 * 40)
payload = bytearray()
for i, (va, size, flags) in enumerate(ranges):
    blob = source[va - 0x400000:va - 0x400000 + size]
    struct.pack_into('<8sIIIIIIHHI', header, sections + i*40, f'.part{i}'.encode(),
                     size, va-0x400000, size, 4096+len(payload),0,0,0,0,flags)
    payload.extend(blob)
target = root / 'room-policy319.exe'
target.write_bytes(header + payload)
metadata = {'version': '3.19.26.22', 'original_sha256': '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537',
            'source_sha256': hashlib.sha256(source).hexdigest(), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
            'ranges': [[hex(a),n] for a,n,_ in ranges],
            'limitations': 'Only original selected pages retained; absent callees/data; static-only, not executable'}
(root/'room-policy-image.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print(json.dumps(metadata))
