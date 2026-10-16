"""Run the captured 3.19 assets reader, never attach to a game process."""
from pathlib import Path
import struct
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parent

class Reader:
    def __init__(self):
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_32)
        self.cpu.mem_map(0, 0x1000000)
        self.cpu.mem_write(0x400000, (ROOT/'analysis-client319.exe').read_bytes())
        self.cpu.mem_map(0x10000000, 0x100000)
        self.cpu.mem_map(0x20000000, 0x2000000)
        self.next = 0x20100000
        self.object = 0x20000000
        self.buffer = 0x20010000
        self.data = 0x20020000
        self.logs = 0
        self.write32(0xca8128, 0xf00000)
        self.write32(0xca8114, 0xf00010)
        for a in (0xf00000, 0xf00010, 0xb74220, 0xb74240, 0xc427f0, 0xc3e400, 0xc42de0, 0xc3c20f, 0x8435d0):
            self.cpu.hook_add(UC_HOOK_CODE, self.hook, begin=a, end=a)

    def u32(self, a): return struct.unpack('<I', self.cpu.mem_read(a,4))[0]
    def write32(self, a, v): self.cpu.mem_write(a,struct.pack('<I',v))
    def hook(self, cpu, address, size, _):
        sp=cpu.reg_read(UC_X86_REG_ESP)
        arg=lambda n:self.u32(sp+4*n)
        result=cpu.reg_read(UC_X86_REG_EAX); pop=0
        if address in (0xf00000,0xf00010):
            result=(self.u32(arg(1))+(1 if address==0xf00000 else -1))&0xffffffff
            self.write32(arg(1),result); pop=4
        elif address==0xb74220:
            result=self.next; self.next+=(arg(1)+15)&~15
            assert self.next<0x22000000
        elif address in (0xc427f0,0xc3e400):
            result=arg(1); cpu.mem_write(result,bytes(cpu.mem_read(arg(2),arg(3))))
        elif address==0xc42de0:
            result=arg(1); cpu.mem_write(result,bytes([arg(2)&255])*arg(3))
        elif address==0x8435d0:
            self.logs+=1
        cpu.reg_write(UC_X86_REG_EAX,result)
        cpu.reg_write(UC_X86_REG_ESP,sp+4+pop)
        cpu.reg_write(UC_X86_REG_EIP,self.u32(sp))

    def call(self, address, this, *args):
        sp=0x100f0000
        self.cpu.mem_write(sp,struct.pack('<'+'I'*(1+len(args)),0xf00100,*args))
        self.cpu.reg_write(UC_X86_REG_ESP,sp)
        self.cpu.reg_write(UC_X86_REG_ECX,this)
        try:self.cpu.emu_start(address,0xf00100,count=100000000)
        except Exception:
            print('EIP',hex(self.cpu.reg_read(UC_X86_REG_EIP)))
            raise
        assert self.cpu.reg_read(UC_X86_REG_EIP)==0xf00100
        return self.cpu.reg_read(UC_X86_REG_EAX)&255

    def parse(self, data):
        self.next=0x20100000
        self.call(0xb8ba90,self.object,1)
        self.cpu.mem_write(self.data,data)
        self.cpu.mem_write(self.buffer,struct.pack('<6I',0,100,len(data),self.data,self.data,self.data+len(data))+b'\1\0\0\0')
        ok=self.call(0xb8bb90,self.object,self.buffer)
        return {'ok':ok,'consumed':self.u32(self.buffer+0x10)-self.data,
                'length':len(data),'count':self.u32(self.object+0x368),'logs':self.logs,
                'items':self.u32(self.object+0x36c)}

if __name__=='__main__':
    r=Reader()
    data=b'\x0a'+struct.pack('<Q',1000001)+b'\x10\0'+b'\x08'+struct.pack('<I',0)+b'\x08'+struct.pack('<I',0)+b'\x06\0\0'
    print(r.parse(data))
