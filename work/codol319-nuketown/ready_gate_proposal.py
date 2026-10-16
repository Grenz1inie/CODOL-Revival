"""Offline-only proposal. Writes Unicorn memory, never a process or EXE file."""
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP

ORIGINAL = bytes.fromhex('558bec83ec08')


def gate(base, cave):
    code = bytearray(b'\x9c\x50\xa1' + struct.pack('<I', base + 0x7ee13fc))
    branches = []
    def condition(opcode):
        branches.append(len(code) + 1)
        code.extend([opcode, 0])
    code.extend(b'\x85\xc0') # Null room: keep original behavior.
    condition(0x74)
    code.extend(b'\x80\xb8' + struct.pack('<I', 0x105fc) + b'\x19') # Playlist110 -> native25.
    condition(0x75)
    code.extend(b'\x81\xb8' + struct.pack('<II', 0xe368, 1000001))
    condition(0x75)
    code.extend(b'\x83\xb8' + struct.pack('<I', 0xe36c) + b'\0')
    condition(0x75)
    code.extend(b'\x83\x79\x20\x02') # Do not interfere after countdown starts.
    condition(0x77)
    code.extend(b'\x80\xb8' + struct.pack('<I', 0xe3f8) + b'\0')
    condition(0x75)
    code.extend(b'\x58\x9d\xc3') # Human not Ready: leave automatic matcher idle.
    resume = len(code)
    for offset in branches:
        code[offset] = resume - offset - 1
    code.extend(b'\x58\x9d' + ORIGINAL)
    entry = base + 0x23c5e0
    code.extend(b'\xe9' + struct.pack('<i', entry + 6 - (cave + len(code) + 5)))
    return bytes(code), b'\xe9' + struct.pack('<i', cave - entry - 5) + b'\x90'


def verify():
    room, controller, cave = 0x20020000, 0x20000000, 0x20180000
    cases = [(25, 0, 1, False), (25, 1, 1, True), (25, 0, 3, True), (26, 0, 1, True)]
    for base in (0x400000, 0x500000):
        machine = InventoryReader319()
        cpu = machine.cpu
        assert bytes(cpu.mem_read(0x63c5e0, 6)) == ORIGINAL
        pointer = base + 0x7ee13fc
        cpu.mem_map(pointer & ~4095, 4096)
        machine.write32(pointer, room) # Heap pointer is not relocated a second time.
        machine.write32(room + 0xe368, 1000001)
        payload, patch = gate(base, cave)
        entry = base + 0x23c5e0
        cpu.mem_write(cave, payload)
        cpu.mem_write(entry, patch)
        reached = []
        def stop(cpu, address, size, user):
            reached.append(True)
            cpu.emu_stop()
        hook = cpu.hook_add(UC_HOOK_CODE, stop, begin=entry+6, end=entry+6)
        for playlist, ready, state, expected in cases:
            reached.clear()
            cpu.mem_write(room + 0x105fc, bytes([playlist]))
            cpu.mem_write(room + 0xe3f8, bytes([ready]))
            machine.write32(controller + 0x20, state)
            machine.write32(0x100f0000, 0xf00100)
            cpu.reg_write(UC_X86_REG_ESP, 0x100f0000)
            cpu.reg_write(UC_X86_REG_ECX, controller)
            cpu.reg_write(UC_X86_REG_EAX, 0x12345678)
            cpu.emu_start(entry, 0xf00100, count=1000)
            assert bool(reached) == expected, (hex(base), playlist, ready, state, hex(cpu.reg_read(UC_X86_REG_EIP)))
            assert cpu.reg_read(UC_X86_REG_EAX) == 0x12345678
            assert cpu.reg_read(UC_X86_REG_ECX) == controller
            assert cpu.reg_read(UC_X86_REG_ESP) == (0x100efff4 if expected else 0x100f0004)
        cpu.hook_del(hook)
    print('8 offline gate cases passed; no process access, EXE changes or live activation')


if __name__ == '__main__':
    verify()
