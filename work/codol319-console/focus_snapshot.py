"""Bound Ghidra analysis to selected current-version consumer code pages."""
from pathlib import Path
import hashlib
import json
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

root = Path(__file__).resolve().parent
image = bytearray((root / 'analysis-client319.exe').read_bytes())
text = bytes(image[4096:4096 + 9072640])
cs = Cs(CS_ARCH_X86, CS_MODE_32)
seeds = [0x7f6330, 0xb8d050, 0x512120, 0x474340, 0x4a6da0, 0x646b00,
         0x631c50, 0x63b630, 0x63b870, 0x67e910, 0x6831e0, 0x6abeb0,
         0x758890, 0x75e250, 0x75e410, 0x776400, 0x7c3730, 0x7c84d0, 0x7cab20]
pages = {p for s in seeds for p in (s & ~0xfff, (s & ~0xfff) + 0x1000)}
for page in list(pages):
    for ins in cs.disasm(text[page - 0x401000:page - 0x401000 + 4096], page):
        if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
            target = int(ins.op_str, 16)
            if 0x401000 <= target < 0xca8000:
                pages.add(target & ~0xfff)
                pages.add((target & ~0xfff) + 0x1000)
image[4096:4096 + 9072640] = b'\xcc' * 9072640
for page in pages:
    offset = page - 0x400000
    image[offset:offset + 4096] = text[page - 0x401000:page - 0x401000 + 4096]
target = root / 'focus-client319.exe'
target.write_bytes(image)
metadata = {'sha256': hashlib.sha256(image).hexdigest(), 'source': 'analysis-image.json',
            'pages': [hex(p) for p in sorted(pages)], 'limitations': 'All other code replaced with INT3 for bounded static analysis; never run this image'}
(root / 'focus-image.json').write_text(json.dumps(metadata, indent=2))
print(len(pages), 'pages', metadata['sha256'])
