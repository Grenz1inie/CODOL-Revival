"""Execute the captured 3.19 profile checksum function offline; no process attachment."""
from pathlib import Path
import hashlib
import json
import struct
import zlib
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import UC_X86_REG_ESP, UC_X86_REG_EDI, UC_X86_REG_EAX

root = Path(__file__).resolve().parents[2]
source = root / 'runtime/instances/codol-3.19.26.22-911c42a0027c/game/code319-44184-stage6-text-00401000.bin'
code = source.read_bytes()
assert hashlib.sha256(code).hexdigest() == '2894b36077fc6fe07e7235bb532c75895928ce69ac0b46bec15184e077199e0c'
vm = Uc(UC_ARCH_X86, UC_MODE_32)
for addr, size in ((0x400000, 0x8a8000), (0x81fe000,0x1000), (0x849b000,0x1000),
                   (0x20000000,0x10000), (0x30000000,0x10000), (0x50000000,0x1000)):
    vm.mem_map(addr,size)
vm.mem_write(0x401000,code)
results = []
for name, data in [('zero',bytes(0x7ffc)), ('pattern',bytes(i%256 for i in range(0x7ffc))),
                   ('changed-field',bytes(4840)+struct.pack('<I',3582550)+bytes(0x7ffc-4844))]:
    vm.mem_write(0x20000090,data)
    vm.mem_write(0x3000f000,struct.pack('<I',0x50000000))
    vm.reg_write(UC_X86_REG_ESP,0x3000f000)
    vm.reg_write(UC_X86_REG_EDI,0x20000000)
    vm.emu_start(0x7f6a70,0x50000000,count=1000000)
    actual = vm.reg_read(UC_X86_REG_EAX)
    expected = zlib.crc32(data)
    assert actual == expected == struct.unpack('<I',vm.mem_read(0x2000008c,4))[0]
    results.append({'case':name,'native':hex(actual),'zlib':hex(expected),'bytes':len(data)})
result = {'version':'3.19.26.22','client_sha256':'36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537',
          'source_sha256':hashlib.sha256(code).hexdigest(),'addresses':['0x7f6a70','0x7bc4d0'],
          'source':'saved stage6 text snapshot executed in Unicorn','coverage':results,
          'unverified':'Network framing/encryption and actual UI consumption are outside this checksum replay'}
(Path(__file__).parent/'native-crc319.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
