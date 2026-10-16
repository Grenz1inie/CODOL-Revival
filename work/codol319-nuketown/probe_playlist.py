from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EIP, UC_X86_REG_EAX
m=InventoryReader319()
m.cpu.mem_map(0x7b25000,0x5000)
m.cpu.mem_map(0x333a000,0x1000)
m.write32(0x333abdc,m.object)
commands=[]
def hook(cpu,address,size,data):
    sp=cpu.reg_read(UC_X86_REG_ESP)
    if address==0x4f3890:
        commands.append(bytes(cpu.mem_read(m.u32(sp+12),256)).split(b'\0')[0].decode())
    cpu.reg_write(UC_X86_REG_EAX,0)
    cpu.reg_write(UC_X86_REG_ESP,sp+4)
    cpu.reg_write(UC_X86_REG_EIP,m.u32(sp))
for a in [0x761740,0x4f3890]:m.cpu.hook_add(UC_HOOK_CODE,hook,begin=a,end=a)
m.cpu.mem_write(m.data,b'3265\0')
for line in [b'party_maxplayers 18\n\0',b'3265 18\n\0']:
    m.cpu.mem_write(0x7b25d00,bytes(2048))
    m.cpu.mem_write(0x7b25d00,line)
    commands.clear()
    m.call(0x761c30,0,m.data)
    print(line,commands)
