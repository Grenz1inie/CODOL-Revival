"""Execute the shipped client's DATA writer, including SHA-1/HMAC/AES-CTR."""
import struct

from client_matchmaking423 import ClientMatchmaking423
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP


class ClientTransport423(ClientMatchmaking423):
    def __init__(self):
        super().__init__()
        # Isolate CRT allocation only; run all packet and crypto code unchanged.
        self.allocation = 0x30100000
        self.cpu.hook_add(UC_HOOK_CODE, self._allocate, begin=0xaf7ca8, end=0xaf7ca8)
        self.cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xaf7c6e, end=0xaf7c6e)

    def _allocate(self, cpu, address, size, context):
        sp = cpu.reg_read(UC_X86_REG_ESP)
        length, = struct.unpack('<I', cpu.mem_read(sp+4, 4))
        result = self.allocation
        self.allocation += (length+15) & ~15
        if self.allocation > 0x30300000:
            raise ValueError('client crypto scratch exhausted')
        self._return(cpu, address, size, context)
        cpu.reg_write(UC_X86_REG_EAX, result)

    def call(self, address, obj, *args):
        stack, end = 0x303ef000, 0x303ffff0
        self.cpu.mem_write(stack, struct.pack('<'+'I'*(1+len(args)), end, *args))
        self.cpu.reg_write(UC_X86_REG_ESP, stack)
        self.cpu.reg_write(UC_X86_REG_ECX, obj)
        self.cpu.emu_start(address, end, count=2000000)
        if self.cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError(f'client transport did not finish: {address:#x}')
        return self.cpu.reg_read(UC_X86_REG_EAX)

    def data_packet(self, key, tag, counter, plain):
        cpu = self.cpu
        self.allocation = 0x30100000
        obj, cipher, source, output = 0x30000000, 0x30001000, 0x30010000, 0x30020000
        keyptr, sequence, used = 0x30003000, 0x30003100, 0x30003200
        cpu.mem_write(obj, bytes(0x4000))
        cpu.mem_write(keyptr, key.ljust(24, b'\0'))
        cpu.mem_write(sequence, struct.pack('<I', counter))
        cpu.mem_write(source, struct.pack('<H', len(plain))+plain)
        self.call(0xb2dae0, cipher)  # bdCypherAESCTR constructor
        if not self.call(0xb2db60, cipher, keyptr, 16) & 255:
            raise ValueError('client AES initialization failed')
        self.call(0xa7f830, obj, tag, counter & 65535)
        if not self.call(0xa7f960, obj, output, 65535, 0, used, sequence,
                         keyptr, source, len(plain)+2, cipher) & 255:
            raise ValueError('client DATA serialization failed')
        length, = struct.unpack('<I', cpu.mem_read(used, 4))
        return bytes(cpu.mem_read(output, length))
