"""Execute shipped MatchMakingInfo readers; no process, socket or Windows API."""
import struct

from client_reader423 import ClientReader423
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_ESP, UC_X86_REG_EIP


class ClientMatchmaking423(ClientReader423):
    def __init__(self):
        super().__init__()
        self.cpu.mem_map(0, 4096)  # Isolated x86 SEH head.
        # InterlockedIncrement/Decrement dependencies; retain real reference counts.
        for import_address, stub, opcode in ((0xb5b0fc, 0x303fe100, b'\xff\x00'),
                                             (0xb5b100, 0x303fe120, b'\xff\x08')):
            self.cpu.mem_write(stub, b'\x8b\x44\x24\x04' + opcode + b'\x8b\x00\xc2\x04\x00')
            self.cpu.mem_write(import_address, struct.pack('<I', stub))
        self.cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xa53d80, end=0xa53d80)

    def candidate(self, wire):
        cpu = self.cpu
        obj, buffer, data, stack, end = 0x30000000, 0x30001000, 0x30002000, 0x303ff000, 0x303ffff0
        cpu.mem_write(obj, bytes(0x228))
        cpu.mem_write(data, wire)
        cpu.mem_write(buffer, struct.pack('<7I', 0, 2, len(wire), data, data, data + len(wire), 1))
        cpu.mem_write(stack, struct.pack('<2I', end, buffer))
        cpu.reg_write(UC_X86_REG_ECX, obj)
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x701db0, end, count=1000000)
        if cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('current MatchMakingInfo reader did not finish')
        cursor = struct.unpack('<I', cpu.mem_read(buffer + 16, 4))[0] - data
        return bool(cpu.reg_read(UC_X86_REG_EAX) & 255), bytes(cpu.mem_read(obj, 0x228)), cursor
