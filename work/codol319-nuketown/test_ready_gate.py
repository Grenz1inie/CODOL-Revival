"""Offline scope and native automatic-state regressions; never opens a process."""
import struct
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319
from ready_gate_proposal import gate, ORIGINAL
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP


class ReadyGateTests(unittest.TestCase):
    def test_scope_preserves_other_rooms_and_nonwaiting_states(self):
        room, controller = 0x20020000, 0x20010000
        for base, cave in ((0x400000,0x20180000), (0x500000,0x20180000), (0x400000,0xf0200000)):
            m = InventoryReader319()
            cpu = m.cpu
            pointer = base + 0x7ee13fc
            cpu.mem_map(pointer & ~4095, 4096)
            if cave == 0xf0200000: cpu.mem_map(cave,4096)
            payload, patch = gate(base, cave)
            entry = base + 0x23c5e0
            cpu.mem_write(cave, payload)
            cpu.mem_write(entry, patch)
            reached = []
            def resume(cpu, address, size, user):
                reached.append(True)
                cpu.emu_stop()
            cpu.hook_add(UC_HOOK_CODE, resume, begin=entry + 6, end=entry + 6)
            # room, playlist, owner, local-host flag, ready, native state, resume?
            cases = [(room, 25, 1000001, 1, 0, 1, False),
                     (room, 25, 1000001, 1, 0, 2, False),
                     (room, 25, 1000001, 1, 1, 1, True),
                     (room, 25, 1000001, 1, 0, 0, True),
                     (room, 25, 1000001, 1, 0, 3, True),
                     (room, 26, 1000001, 1, 0, 1, True),
                     (room, 25, 1000002, 1, 0, 1, True),
                     (room, 25, 1000001, 0, 0, 1, True),
                     (0, 25, 1000001, 1, 0, 1, True)]
            for current, playlist, owner, host, ready, state, expected in cases:
                with self.subTest(base=hex(base), current=current, playlist=playlist,
                                  owner=owner, host=host, ready=ready, state=state):
                    reached.clear()
                    m.write32(pointer, current)
                    cpu.mem_write(room + 0xe368, struct.pack('<Q', owner))
                    cpu.mem_write(room + 0x281, bytes([host]))
                    cpu.mem_write(room + 0x105fc, bytes([playlist]))
                    cpu.mem_write(room + 0xe3f8, bytes([ready]))
                    m.write32(controller + 0x20, state)
                    m.write32(0x100f0000, 0xf00100)
                    cpu.reg_write(UC_X86_REG_ESP, 0x100f0000)
                    cpu.reg_write(UC_X86_REG_ECX, controller)
                    cpu.reg_write(UC_X86_REG_EAX, 0x12345678)
                    cpu.emu_start(entry, 0xf00100, count=1000)
                    self.assertEqual(bool(reached), expected)
                    self.assertEqual(cpu.reg_read(UC_X86_REG_EAX), 0x12345678)
                    self.assertEqual(cpu.reg_read(UC_X86_REG_ECX), controller)
                    self.assertEqual(cpu.reg_read(UC_X86_REG_ESP),
                                     0x100efff4 if expected else 0x100f0004)

    def test_native_automatic_state_waits_until_human_ready(self):
        m = InventoryReader319()
        cpu, room, controller, table = m.cpu, 0x20020000, 0x20010000, 0x20050000
        for page in (0x82e1000, 0x7644000):
            cpu.mem_map(page, 4096)
        m.write32(0x82e13fc, room)
        m.write32(room, table)
        cpu.mem_write(room + 0x281, b'\1')
        cpu.mem_write(room + 0x105fc, b'\x19')
        cpu.mem_write(room + 0x10614, b'\1')
        m.write32(room + 0xe368, 1000001)
        for offset, target in ((0x60, 0xf00300), (0x64, 0x62fe80), (0x54, 0xf00300),
                               (0xd8, 0xf00310), (0xdc, 0xf00310)):
            m.write32(table + offset, target)
        # Only environmental/group eligibility and clocks are stubbed. The real
        # 0x63c5e0 decision and 0x63c5b0 state transition execute unchanged.
        cpu.mem_write(0xf00400, b'\xd9\xee\xc3')  # fldz; ret
        def environment(cpu, address, size, user):
            if address == 0xb75da0:
                cpu.reg_write(UC_X86_REG_EIP, 0xf00400)
                return
            cpu.reg_write(UC_X86_REG_EAX, int(address in (0xf00300, 0x63c550)))
            sp = cpu.reg_read(UC_X86_REG_ESP)
            cpu.reg_write(UC_X86_REG_ESP, sp + 4)
            cpu.reg_write(UC_X86_REG_EIP, m.u32(sp))
        for address in (0xf00300, 0xf00310, 0x771320, 0xc42d30,
                        0xb75da0, 0xb75d80, 0x63c550):
            cpu.hook_add(UC_HOOK_CODE, environment, begin=address, end=address)
        m.write32(controller + 0x20, 1)
        m.call(0x63c5e0, controller)
        self.assertEqual(m.u32(controller + 0x20), 3,
                         'Original automatic branch starts with every member unready')
        m.write32(controller + 0x20, 1)
        payload, patch = gate(0x400000, 0x20180000)
        self.assertEqual(bytes(cpu.mem_read(0x63c5e0, 6)), ORIGINAL)
        cpu.mem_write(0x20180000, payload)
        cpu.mem_write(0x63c5e0, patch)
        cpu.ctl_remove_cache(0x63c5e0, 0x63c5e6)
        for _ in range(3):
            m.call(0x63c5e0, controller)
            self.assertEqual(m.u32(controller + 0x20), 1)
        cpu.mem_write(room + 0xe3f8, b'\1')
        m.call(0x63c5e0, controller)
        self.assertEqual(m.u32(controller + 0x20), 3)


if __name__ == '__main__':
    unittest.main()
