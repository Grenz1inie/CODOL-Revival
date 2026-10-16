"""Current client hash and stats writer, isolated in Unicorn (no game process)."""
import struct
from client_reader423 import ClientReader423
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESI, UC_X86_REG_ESP, UC_X86_REG_EIP


class ClientConnection423(ClientReader423):
    def frame_milliseconds(self, raw_msec):
        """Run the stock slow-motion config consumer and common frame clock."""
        cpu = self.cpu
        stack, end, dvars = 0x303ff000, 0x303ffff0, 0x302b0000
        for i, pointer in enumerate((0x2e8a98c, 0x2e8a998, 0x2e8cfc0)):
            address = dvars + i*0x40
            cpu.mem_write(pointer, struct.pack('<I', address))
            cpu.mem_write(address, bytes(0x40))
            cpu.mem_write(address+12, struct.pack('<f', 0. if i == 0 else 1.))
        cpu.mem_write(0x2e8cf70, bytes(0x34))
        cpu.mem_write(0x2e8a96c, bytes(4))
        for address in (0x2e8a974, 0x2e8cf88, 0xcdcd3c):
            cpu.mem_write(address, struct.pack('<f', 1.))
        # Real missing-config failure leaves these four sscanf destinations
        # uninitialized. Seed the observed scale words, not a zero-filled stack.
        cpu.mem_write(stack-20, struct.pack('<iiII', 0, 0, 0x01d210e0, 0x01d2447c))
        cpu.mem_write(stack, struct.pack('<I', end))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x579f30, 0x579f57, count=10000)
        if cpu.reg_read(UC_X86_REG_EIP) != 0x579f57:
            raise ValueError('native slow-motion parser did not reach sscanf')
        sp = cpu.reg_read(UC_X86_REG_ESP)
        text, fmt, *destinations = struct.unpack('<6I', cpu.mem_read(sp, 24))
        if bytes(cpu.mem_read(fmt, 12)).split(b'\0')[0] != b'%i %i %g %g':
            raise ValueError('unexpected native clock format')
        values = bytes(cpu.mem_read(text, 128)).split(b'\0')[0].split()
        # Replace only CRT sscanf (Windows TLS); the config lookup, scheduling
        # and millisecond conversion below execute unchanged client code.
        for i, value in enumerate(values[:4]):
            cpu.mem_write(destinations[i], struct.pack('<i' if i < 2 else '<f',
                int(value) if i < 2 else float(value)))
        cpu.reg_write(UC_X86_REG_EAX, min(len(values), 4))
        cpu.emu_start(0x579f5c, end, count=10000)
        cpu.mem_write(stack, struct.pack('<II', end, raw_msec))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x59d500, end, count=10000)
        if cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('native frame clock did not finish')
        return cpu.reg_read(UC_X86_REG_EAX)

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
