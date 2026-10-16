from pathlib import Path
import json, struct, sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319
m = InventoryReader319()
human = bytes.fromhex(json.loads((Path(__file__).parent/'room-context-81072.json').read_text())['players'][0]['bytes'])
obj, ref, string = m.object, 0x2001f000, 0x2001e000
m.cpu.mem_write(obj+0x10, human)
m.cpu.mem_write(obj+0x10, struct.pack('<Q',0x600000001))
m.write32(obj+0x98,1)
m.cpu.mem_write(obj+0xa0,b'\x01')
m.cpu.mem_write(obj+0x58, bytes(64))
m.write32(obj,0xdc75a0)
m.write32(obj+4,6)
m.write32(obj+8,1)
m.cpu.mem_write(string,struct.pack('<III',1,0,1)+b'\0')
m.write32(obj+0xc,string+12)
m.write32(obj+0x1e4,797)
m.cpu.mem_write(obj+0x1e0,human[0x94:0x96])
m.call(0xb778e0,m.buffer,0x10000,0)
m.write32(ref,m.buffer)
m.call(0x6270d0,obj,ref)
wire = bytes(m.cpu.mem_read(m.u32(m.buffer+8),m.u32(m.buffer+0x10)))
print('writer',len(wire),m.u32(m.buffer+0x14),wire.hex())
m.cpu.mem_write(m.data,wire)
m.call(0xb779a0,m.buffer,m.data,len(wire)*8,1)
out = 0x20005000
m.call(0x623770,out+0x10)
m.write32(out+0xc,string+12)
print('reader',m.call(0x627230,out,ref),'bits',m.u32(m.buffer+0x1c),'logs',m.logs)
print('state',bytes(m.cpu.mem_read(out+0x10,0x1d0)).hex())
print('trailing',bytes(m.cpu.mem_read(out+0x1e0,20)).hex())
(Path(__file__).parent/'join-native.bin').write_bytes(wire)
