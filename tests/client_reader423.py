"""Execute the shipped client's configstring reader without starting the game."""
import hashlib
from pathlib import Path
import struct
import sys

import pefile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/experiments/story-native/python-libs'))
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EAX, UC_X86_REG_ESI,
                               UC_X86_REG_ESP, UC_X86_REG_EBP, UC_X86_REG_EIP)


class ClientReader423:
    """No socket, file, renderer, or Windows API executes in this emulator."""
    def __init__(self):
        path = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b':
            raise ValueError('client hash mismatch')
        pe = pefile.PE(data=data, fast_load=True)
        self.player_fields = list(struct.iter_unpack('<iii', pe.get_data(
            0xc55f70 - pe.OPTIONAL_HEADER.ImageBase, 235 * 12)))
        self.event_widths = list(struct.unpack('<162I', pe.get_data(
            0xc56d70-pe.OPTIONAL_HEADER.ImageBase, 162*4)))
        self.kinds = bytearray([255]) * 7058
        layout = pe.get_data(0xc57118 - pe.OPTIONAL_HEADER.ImageBase, 21 * 12)
        for kind, (start, capacity, reserved) in enumerate(struct.iter_unpack('<3I', layout)):
            self.kinds[start:start + capacity] = bytes([kind]) * capacity
        self.cpu = Uc(UC_ARCH_X86, UC_MODE_32)
        base = pe.OPTIONAL_HEADER.ImageBase
        self.cpu.mem_map(base, (pe.OPTIONAL_HEADER.SizeOfImage + 4095) & ~4095)
        self.cpu.mem_write(base, data[:pe.OPTIONAL_HEADER.SizeOfHeaders])
        for section in pe.sections:
            self.cpu.mem_write(base + section.VirtualAddress, section.get_data())
        self.cpu.mem_map(0x30000000, 0x400000)
        self.cpu.hook_add(UC_HOOK_CODE, self._error, begin=0x597d20, end=0x597d20)
        self.cpu.hook_add(UC_HOOK_CODE, self._format, begin=0x637c20, end=0x637c20)
        # UI notification, disconnect/reset, empty spawn-origin sscanf, and
        # post-parse setup are outside this wire seam. No reader/CRC is replaced.
        for address in (0x637c60, 0x5a6510, 0x464420, 0x59e700, 0xaf8ca9,
                        0x46de40, 0x49f930, 0x46d830, 0x46d860):
            self.cpu.hook_add(UC_HOOK_CODE, self._return, begin=address, end=address)
        self.cpu.mem_write(0x303fe000, b'\x31\xc0\xc3')  # Return 0 for clock/thread ID.
        for address in (0xb5b468, 0xb5b194):
            self.cpu.mem_write(address, struct.pack('<I', 0x303fe000))
        self.error = False

    def usercmd(self, values, *, key, base=None):
        """Run the shipped 0x5a1be0 writer; inputs use its real usercmd layout."""
        cpu = self.cpu
        msg, data, source, dest = 0x30000000, 0x30001000, 0x30280000, 0x30290000
        stack, end = 0x303ff000, 0x303ffff0
        offsets = {'time': (0, 'I'), 'buttons': (4, 'I'), 'pitch': (8, 'I'),
                   'yaw': (12, 'I'), 'roll': (16, 'I'), 'weapon': (20, 'H'),
                   'alt': (22, 'H'), 'offhand': (24, 'H'), 'forward': (26, 'b'),
                   'right': (27, 'b'), 'melee_yaw': (28, 'f'), 'melee_dist': (32, 'B'),
                   'melee_target': (34, 'H'), 'location_x': (36, 'B'),
                   'location_y': (37, 'B'), 'location_angle': (38, 'B'),
                   'remote_x': (39, 'B'), 'remote_y': (40, 'B')}
        for address, command in ((source, base or {}), (dest, values)):
            cpu.mem_write(address, bytes(44))
            for field, value in command.items():
                offset, form = offsets[field]
                cpu.mem_write(address + offset, struct.pack('<' + form, value))
        cpu.mem_write(msg, struct.pack('<12I', 0, 0, data, 0, 4096, 0, 0, 0, 0, 0, 0, 0))
        cpu.mem_write(stack, struct.pack('<III', end, key, source))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_EAX, msg)
        cpu.reg_write(UC_X86_REG_ESI, dest)
        cpu.emu_start(0x5a1be0, end, count=100000)
        overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
        if overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client failed to encode usercmd')
        size, = struct.unpack('<I', cpu.mem_read(msg + 20, 4))
        return bytes(cpu.mem_read(data, size))

    def default_usercmd(self, fields):
        cpu = self.cpu
        source, dest, stack, end = 0x30280000, 0x30290000, 0x303ff000, 0x303ffff0
        cpu.mem_write(source, bytes(0x3524))
        for i, value in fields.items():
            offset, bits, _ = self.player_fields[i]
            cpu.mem_write(source+offset, struct.pack('<Q' if bits==-94 else '<I', value))
        cpu.mem_write(stack,struct.pack('<I',end))
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.reg_write(UC_X86_REG_ESI,dest)
        cpu.reg_write(UC_X86_REG_EDI,source)
        cpu.emu_start(0x5a18e0,end,count=100000)
        if cpu.reg_read(UC_X86_REG_EIP)!=end:
            raise ValueError('client default usercmd did not finish')
        command=bytes(cpu.mem_read(dest,44))
        time,buttons,pitch,yaw,roll,weapon,alt,offhand=struct.unpack_from('<5I3H',command)
        melee,=struct.unpack_from('<H',command,34)
        return [time,buttons,pitch,yaw,roll,0,weapon,offhand,alt,0,0,melee,*command[36:41]]

    def _init_player(self, state, protected_value=0):
        cpu = self.cpu
        floats, stack, end = 0x302a0000, 0x303ff000, 0x303ffff0
        cpu.mem_write(state, bytes(0x3524))
        obj = state + 536
        keys = struct.unpack('<II', cpu.mem_read(0xce5184, 8))
        cpu.mem_write(obj + 16, struct.pack('<II', (obj + 20) ^ keys[0] ^ 0x401710,
                                            (obj + 16) ^ keys[1] ^ 0x4017b0))
        cpu.mem_write(floats, struct.pack('<3f', protected_value, 1., 2.))
        cpu.mem_write(stack, struct.pack('<III', end, floats, obj))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x401710, end, count=10000)

    def playerstate(self, wire, *, server_time, base=None):
        cpu = self.cpu
        msg, data, stack, end = 0x30000000, 0x30001000, 0x303ff000, 0x303ffff0
        source, dest, floats = 0x30280000, 0x30290000, 0x302a0000
        # Deterministic seed only; protected-value storage and every network
        # reader still execute the shipped machine code.
        hook = cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xa6e160, end=0xa6e160)
        try:
            for state in (source, dest):
                self._init_player(state, (base or {}).get(82, 0))
            for index, value in (base or {}).items():
                if index == 82:
                    continue
                offset, bits, _ = self.player_fields[index]
                cpu.mem_write(source + offset, struct.pack('<Q' if bits == -94 else '<I', value))
            self.error = False
            cpu.mem_write(data, wire)
            cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 0, 0, 0, 0, 0))
            cpu.mem_write(stack, struct.pack('<III', end, server_time, source))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, dest)
            cpu.reg_write(UC_X86_REG_ESI, msg)
            cpu.emu_start(0x5a4230, end, count=2000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
                raise ValueError('client rejected playerstate')
            result = [struct.unpack('<Q' if bits == -94 else '<I',
                                    cpu.mem_read(dest + o, 8 if bits == -94 else 4))[0]
                      for o, bits, _ in self.player_fields]
            # The protected byte's getter returns the logical float value.
            cpu.mem_write(stack, struct.pack('<III', end, dest + 536, floats))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.emu_start(0x4017b0, end, count=10000)
            result[82] = int(struct.unpack('<f', cpu.mem_read(floats, 4))[0])
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            return result, wire[cursor:]
        finally:
            cpu.hook_del(hook)

    def _return(self, cpu, address, size, context):
        stack = cpu.reg_read(UC_X86_REG_ESP)
        ret, = struct.unpack('<I', cpu.mem_read(stack, 4))
        cpu.reg_write(UC_X86_REG_EAX, 0)
        cpu.reg_write(UC_X86_REG_ESP, stack + 4)
        cpu.reg_write(UC_X86_REG_EIP, ret)

    def _error(self, cpu, address, size, context):
        self.error = True
        cpu.emu_stop()

    def _format(self, cpu, address, size, context):
        # Replace only the CRT formatting dependency, which needs Windows TLS.
        # Network fields and their bit widths are still read by original code.
        stack = cpu.reg_read(UC_X86_REG_ESP)
        ret, end, fmt = struct.unpack('<3I', cpu.mem_read(stack, 12))
        pattern = bytes(cpu.mem_read(fmt, 32)).split(b'\0', 1)[0]
        if pattern not in (b'* %i', b'** %i %i %i', b' %i'):
            raise ValueError(f'unhandled client format {pattern!r}')
        count = pattern.count(b'%i')
        values = struct.unpack('<' + 'I' * count, cpu.mem_read(stack + 12, 4 * count))
        dest = cpu.reg_read(UC_X86_REG_EDI)
        text = pattern % values
        if len(text) >= end - dest:
            raise ValueError('format buffer overflow')
        cpu.mem_write(dest, text + b'\0')
        cpu.reg_write(UC_X86_REG_EAX, dest + len(text))
        cpu.reg_write(UC_X86_REG_ESP, stack + 4)
        cpu.reg_write(UC_X86_REG_EIP, ret)

    def configstrings(self, wire, kinds=None):
        cpu = self.cpu
        self.error = False
        msg, data, stack, end = 0x30000000, 0x30001000, 0x303ff000, 0x303ffff0
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<10I', 0, 1, data, 0, len(wire), len(wire), 0, 0, 0, 0))
        cpu.mem_write(0x2df7da0, bytes(self.kinds) if kinds is None else kinds)
        cpu.mem_write(stack, struct.pack('<I', end))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_ECX, msg)
        cpu.emu_start(0x46db20, end, count=2000000)
        overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
        if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client rejected configstrings')
        offsets = struct.unpack('<7058I', cpu.mem_read(0x796f2dc, 7058 * 4))
        size, = struct.unpack('<I', cpu.mem_read(0x7996124, 4))
        pool = bytes(cpu.mem_read(0x7976124, size))
        rows = {i: pool[o:pool.index(0, o)].decode('ascii') for i, o in enumerate(offsets) if o}
        cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
        return rows, wire[cursor:]

    def gamestate(self, wire, *, checksum):
        """Stop at loading-screen archive setup, before world/renderer loading."""
        cpu = self.cpu
        msg, data, conn, stack, end = 0x30000000, 0x30001000, 0x30100000, 0x303ff000, 0x303ffff0
        self.error = False
        selected = {}
        def text(address):
            return bytes(cpu.mem_read(address, 64)).split(b'\0', 1)[0].decode('ascii')
        def loading(cpu, address, size, context):
            selected.update(map=text(cpu.reg_read(UC_X86_REG_EDI)),
                            game_type=text(cpu.reg_read(UC_X86_REG_EBP) - 0x88))
            cpu.emu_stop()
        hook = cpu.hook_add(UC_HOOK_CODE, loading, begin=0x4651b0, end=0x4651b0)
        try:
            cpu.mem_write(data, wire)
            cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 1, 0, 0, 0, 0))
            for address, value in ((0x1a2a538, conn ^ 0xd362501f), (0x1a2e7ec, 7),
                                   (0x2df9934, 1), (0x2df7d90, checksum), (0x788c760, 1),
                                   (0x35f2238, 0x30180000), (0x78b0bb8, 0)):
                cpu.mem_write(address, struct.pack('<I', value))
            cpu.mem_write(0x1a2e7dd, bytes(4))
            cpu.mem_write(0x17cd27e, b'\0')
            cpu.mem_write(0x2df7da0, bytes(self.kinds))
            cpu.mem_write(stack, struct.pack('<I', end))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, msg)
            cpu.emu_start(0x46dea0, end, count=2000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or not selected:
                raise ValueError('client rejected gamestate')
            for name, offset in (('command_sequence', 0x4014c), ('client_number', 4), ('checksum_feed', 0x13c)):
                selected[name], = struct.unpack('<I', cpu.mem_read(conn + offset, 4))
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            selected['remaining'] = wire[cursor:]
            return selected
        finally:
            cpu.hook_del(hook)

    def reset_netchan(self):
        cpu = self.cpu
        chan = 0x30180158
        cpu.mem_write(chan, bytes(0x6c8))
        cpu.mem_write(chan + 0x30, struct.pack('<II', 0x30200000, 0x20000))
        cpu.mem_write(0x788c760, struct.pack('<I', 1))
        cpu.mem_write(0xca19520, struct.pack('<I', 1))

    def snapshot(self, wire, *, sequence):
        cpu = self.cpu
        msg, data, conn, client = 0x30000000, 0x30001000, 0x30100000, 0x30240000
        stack, end = 0x303ff000, 0x303ffff0
        cpu.mem_write(client, bytes(0x9000))
        # One real snapshot-ring slot, no prior network history.
        for offset, value in ((0x8664, 1), (0x8668, 0),
                              (0x8680, 0x30260000 ^ 0x336f4a9b),
                              (0x867c, 0x30270000 ^ 0x96b9dc91)):
            cpu.mem_write(client + offset, struct.pack('<I', value))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        cpu.mem_write(0x1a2e838, struct.pack('<I', client ^ 0x6891d1c7))
        cpu.mem_write(conn + 0x40148, struct.pack('<I', sequence))
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, len(wire), len(wire), 0, 1, 0, 0, 0, 0))
        self.error = False
        hook = cpu.hook_add(UC_HOOK_CODE, self._return, begin=0xa6e160, end=0xa6e160)
        try:
            self._init_player(client + 12)
            self._init_player(0x30260000)
            cpu.mem_write(stack, struct.pack('<I', end))
            cpu.reg_write(UC_X86_REG_ESP, stack)
            cpu.reg_write(UC_X86_REG_ECX, msg)
            cpu.emu_start(0x46d170, end, count=2000000)
            overflow, = struct.unpack('<I', cpu.mem_read(msg, 4))
            if self.error or overflow or cpu.reg_read(UC_X86_REG_EIP) != end:
                raise ValueError('client rejected snapshot')
            result = {}
            for name, offset in (('command_time', 0), ('flags', 0x3528),
                                 ('server_time', 0x352c), ('sequence', 0x3530),
                                 ('entities', 0x3540), ('clients', 0x3544), ('actors', 0x3548)):
                result[name], = struct.unpack('<I', cpu.mem_read(0x7996128 + offset, 4))
            cursor, = struct.unpack('<I', cpu.mem_read(msg + 28, 4))
            result['remaining'] = wire[cursor:]
            return result
        finally:
            cpu.hook_del(hook)

    def packet(self, wire, *, challenge, command=b''):
        """Run actual netchan/reassembly and XOR; keep channel state across calls."""
        cpu = self.cpu
        msg, data, conn, stack, end = 0x30000000, 0x30001000, 0x30100000, 0x303ff000, 0x303ffff0
        self.error = False
        cpu.mem_write(data, wire)
        cpu.mem_write(msg, struct.pack('<12I', 0, 1, data, 0, 0x20000, len(wire), 0, 0, 0, 0, 0, 0))
        cpu.mem_write(stack, struct.pack('<II', end, conn + 0x80158))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.reg_write(UC_X86_REG_EDI, msg)
        cpu.emu_start(0x5a5960, end, count=2000000)
        if self.error or cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client netchan failed')
        if not cpu.reg_read(UC_X86_REG_EAX):
            return None
        overflow, _, _, _, _, size = struct.unpack('<6I', cpu.mem_read(msg, 24))
        if overflow or size < 8 or size > 0x20000:
            raise ValueError('client netchan overflow')
        sequence, ack = struct.unpack('<II', cpu.mem_read(data, 8))
        cpu.mem_write(0x1a2a538, struct.pack('<I', conn ^ 0xd362501f))
        for offset, value in ((0x138, challenge), (0x40148, sequence), (0x144, ack)):
            cpu.mem_write(conn + offset, struct.pack('<I', value))
        cpu.mem_write(conn + 0x148 + (ack & 255) * 1024, command + b'\0')
        cpu.mem_write(stack, struct.pack('<III', end, data + 8, size - 8))
        cpu.reg_write(UC_X86_REG_ESP, stack)
        cpu.emu_start(0x46bf80, end, count=2000000)
        if cpu.reg_read(UC_X86_REG_EIP) != end:
            raise ValueError('client decryptor did not finish')
        return sequence, ack, bytes(cpu.mem_read(data + 8, size - 8))
