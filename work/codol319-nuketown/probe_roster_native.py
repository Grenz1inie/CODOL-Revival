"""Execute captured room writers/readers only in Unicorn, never a live process."""
from pathlib import Path
import hashlib
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319

m = InventoryReader319()
rows,reference = 0x20020000,0x2001f000
for slot in range(18):
    row = rows+slot*0x1d0
    m.call(0x623770,row)
    uid = 1_000_001 if slot==0 else 0x600000000+slot
    m.cpu.mem_write(row,struct.pack('<Q',uid))
    m.cpu.mem_write(row+8,('Player' if slot==0 else f'Bot{slot:02}').encode()+b'\0')
    m.write32(row+0x88,1 if slot<9 else 2)
    m.cpu.mem_write(row+0x90,b'\x01')
m.call(0xb778e0,m.buffer,0x10000,0)
m.write32(reference,m.buffer)
m.cpu.mem_write(m.object,struct.pack('<4I',0xdc760c,14,18,rows))
ok = m.call(0x627d80,m.object,reference)
header=[m.u32(m.buffer+i*4) for i in range(9)]
payload=bytes(m.cpu.mem_read(m.u32(m.buffer+8),m.u32(m.buffer+0x10)))
print({'writer_return':ok,'header':header,'length':len(payload),'hex':payload.hex()[:100]})
Path(__file__).with_name('roster-native.bin').write_bytes(payload)
m.cpu.mem_write(m.data,payload)
m.call(0xb779a0,m.buffer,m.data,len(payload)*8,1)
m.cpu.mem_write(m.object,struct.pack('<4I',0xdc760c,14,0,rows+0x3000))
for slot in range(18): m.call(0x623770,rows+0x3000+slot*0x1d0)
ok=m.call(0x627e00,m.object,reference)
members=[]
for slot in range(m.u32(m.object+8)):
    row=rows+0x3000+slot*0x1d0
    members.append({'uid':struct.unpack('<Q',m.cpu.mem_read(row,8))[0],
        'name':bytes(m.cpu.mem_read(row+8,64)).split(b'\0')[0].decode(),
        'team':m.u32(row+0x88),'ready':bytes(m.cpu.mem_read(row+0x90,1))[0]})
result={'writer':hex(0x627d80),'reader':hex(0x627e00),'member_reader':hex(0x623de0),
        'version':'3.19.26.22','sha256':hashlib.sha256(payload).hexdigest(),
        'bytes':len(payload),'reader_return':ok,'reader_bits':m.u32(m.buffer+0x1c),
        'logs':m.logs,'members':members,'unverified':'Live room routing and UI'}
Path(__file__).with_name('roster-native.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
