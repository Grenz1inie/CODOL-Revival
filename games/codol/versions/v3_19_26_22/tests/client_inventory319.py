"""Run the captured 3.19 assets reader, never attach to a game process."""
from pathlib import Path
import struct
import hashlib
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP

ROOT = Path(__file__).resolve().parents[5]
CAPTURE = ROOT / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game'
SNAPSHOTS = (
    ('code319-44184-stage6-text-00401000.bin', 0x401000, '2894b36077fc6fe07e7235bb532c75895928ce69ac0b46bec15184e077199e0c'),
    ('code319-44184-stage6-rdata-00ca8000.bin', 0xca8000, '0e24e7a86acb4a13d851bad92935cef4169865082a3aca3153970b7687f309b2'),
)

class InventoryReader319:
    def __init__(self):
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_32)
        self.cpu.mem_map(0, 0x1000000)
        for name, address, digest in SNAPSHOTS:
            data = (CAPTURE / name).read_bytes()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('3.19 inventory snapshot hash mismatch: ' + name)
            self.cpu.mem_write(address, data)
        exe = (CAPTURE / 'codoMP_client_shipRetail.exe').read_bytes()
        if hashlib.sha256(exe).hexdigest() != '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537':
            raise ValueError('3.19 inventory executable hash mismatch')
        # File-backed data includes the native inflate masks/tables at 00E4FF48.
        self.cpu.mem_write(0xe16000, exe[0x702000:0x764000])
        self.cpu.mem_map(0x10000000, 0x100000)
        self.cpu.mem_map(0x20000000, 0x2000000)
        self.next = 0x20100000
        self.object = 0x20000000
        self.buffer = 0x20010000
        self.data = 0x21000000
        self.logs = 0
        self.write32(0xca8128, 0xf00000)
        self.write32(0xca8114, 0xf00010)
        for a in (0xf00000, 0xf00010, 0xb74220, 0xb74240, 0xc3d280, 0xc3d246,
                  0xc427f0, 0xc3e400, 0xc42de0, 0x769840, 0xc3c20f, 0x8435d0):
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
        elif address in (0xb74220,0xc3d280):
            result=self.next; self.next+=(arg(1)+15)&~15
            assert self.next<self.data
        elif address in (0xc427f0,0xc3e400):
            result=arg(1); cpu.mem_write(result,bytes(cpu.mem_read(arg(2),arg(3))))
        elif address in (0xc42de0,0x769840):
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
        except Exception as error:
            raise RuntimeError(f'Native assets reader stopped at {self.cpu.reg_read(UC_X86_REG_EIP):#x}') from error
        assert self.cpu.reg_read(UC_X86_REG_EIP)==0xf00100
        return self.cpu.reg_read(UC_X86_REG_EAX)&255

    def parse(self, data):
        self.next=0x20100000
        self.logs=0
        self.call(0xb8ba90,self.object,1)
        self.cpu.mem_write(self.data,data)
        self.cpu.mem_write(self.buffer,struct.pack('<6I',0xdb7154,100,len(data),self.data,self.data,self.data+len(data))+b'\1\0\0\0')
        ok=self.call(0xb8bb90,self.object,self.buffer)
        return {'ok':ok,'consumed':self.u32(self.buffer+0x10)-self.u32(self.buffer+0xc),
                'length':len(data),'count':self.u32(self.object+0x368),'logs':self.logs,
                'items':self.u32(self.object+0x36c)}

    def item(self, address):
        return {
            'owner': struct.unpack('<Q', self.cpu.mem_read(address+0x30,8))[0],
            'id': self.u32(address+0x40), 'quantity': self.u32(address+0x44),
            'experience': self.u32(address+0x48), 'expiry': self.u32(address+0x90),
            'usage': struct.unpack('<q', self.cpu.mem_read(address+0x98,8))[0],
            'expiry_duration': self.u32(address+0xa4), 'status': self.u32(address+0xa8),
        }
