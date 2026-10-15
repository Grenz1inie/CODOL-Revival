"""Current client hash and stats writer, isolated in Unicorn (no game process)."""
import struct
from client_reader423 import ClientReader423
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP


class ClientConnection423(ClientReader423):
    def tiger(self, value):
        cpu = self.cpu
        state, data, digest, stack, end = 0x30000000, 0x30001000, 0x30002000, 0x303ff000, 0x303ffff0
        cpu.mem_write(state, bytes(512))
        cpu.mem_write(data, value)
        for address, args in ((0xa87020, [state]), (0xa87060, [state, data, len(value)]),
                              (0xa87110, [state, digest])):
            cpu.mem_write(stack, struct.pack('<'+'I'*(1+len(args)), end, *args))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.emu_start(address, end, count=1000000)
            if cpu.reg_read(UC_X86_REG_EIP) != end or cpu.reg_read(UC_X86_REG_EAX):
                raise ValueError('current Tiger hash did not finish')
        return bytes(cpu.mem_read(digest, 24))

    def stats_fragment(self, profile, index, *, compressed=True):
        cpu = self.cpu
        state, msg, data, source, stack, end = 0x30000000, 0x30010000, 0x30011000, 0x30100000, 0x303ff000, 0x303ffff0
        cpu.mem_write(state, bytes(0x9120))
        cpu.mem_write(source, profile)
        if not compressed:
            cpu.mem_write(state+0x7c, profile)
        for offset, value in ((0x74, 4), (0x9088, source), (0x908c, len(profile) if compressed else 0),
                              (0x909c, 1 << index)):
            cpu.mem_write(state+offset, struct.pack('<I', value))
        cpu.mem_write(msg, struct.pack('<12I', 0, 0, data, 0, 4096, 0, 0, 0, 0, 0, 0, 0))
        cpu.mem_write(0x78b0a58, struct.pack('<I', 1000))
        cpu.mem_write(stack, struct.pack('<I', end))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_ESI, msg)
        cpu.reg_write(UC_X86_REG_EAX, state)
        cpu.emu_start(0x6d81a0, end, count=1000000)
        if cpu.reg_read(UC_X86_REG_EIP) != end or struct.unpack('<I', cpu.mem_read(msg, 4))[0]:
            raise ValueError('current stats writer did not finish')
        size, = struct.unpack('<I', cpu.mem_read(msg+20, 4))
        return bytes(cpu.mem_read(data, size))
