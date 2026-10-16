"""Replay 3.19 room writers/readers in Unicorn using hash-bound local snapshots."""
import struct
import sys
from client_inventory319 import InventoryReader319


def verify(payload, human):
    machine = InventoryReader319()
    rows, reference = 0x20020000, 0x2001f000
    for slot in range(18):
        row = rows + slot * 0x1d0
        machine.call(0x623770, row)
        if slot == 0:
            machine.cpu.mem_write(row, human)
        else:
            machine.cpu.mem_write(row + 0x90, b'\x01')
        machine.cpu.mem_write(row, struct.pack('<Q', 1_000_001 if slot == 0 else 0x600000000 + slot))
        machine.write32(row + 0x88, 1 if slot < 9 else 2)
    machine.call(0xb778e0, machine.buffer, 0x10000, 0)
    machine.write32(reference, machine.buffer)
    machine.cpu.mem_write(machine.object, struct.pack('<4I', 0xdc760c, 14, 18, rows))
    machine.call(0x627d80, machine.object, reference)
    native = bytes(machine.cpu.mem_read(machine.u32(machine.buffer + 8), machine.u32(machine.buffer + 0x10)))
    assert payload == native, 'Rust roster differs from native writer 0x627d80'
    assert machine.u32(machine.buffer + 0x14) == 9851

    machine.cpu.mem_write(machine.data, payload)
    machine.call(0xb779a0, machine.buffer, machine.data, len(payload) * 8, 1)
    output = rows + 0x3000
    for slot in range(18):
        machine.call(0x623770, output + slot * 0x1d0)
    machine.cpu.mem_write(machine.object, struct.pack('<4I', 0xdc760c, 14, 0, output))
    assert machine.call(0x627e00, machine.object, reference) == 1
    assert machine.u32(machine.object + 8) == 18
    assert machine.u32(machine.buffer + 0x1c) == 9851
    assert machine.logs == 0
    for slot in range(18):
        row = output + slot * 0x1d0
        assert struct.unpack('<Q', machine.cpu.mem_read(row, 8))[0] == (1_000_001 if slot == 0 else 0x600000000 + slot)
        assert machine.u32(row + 0x88) == (1 if slot < 9 else 2)
        assert bytes(machine.cpu.mem_read(row + 0x90, 1)) == (human[0x90:0x91] if slot == 0 else b'\x01')
        # Names are populated by channel membership, not this room message.
        assert bytes(machine.cpu.mem_read(row + 8, 1)) == b'\0'
    assert bytes(machine.cpu.mem_read(output + 0x94, 4)) == human[0x94:0x98]
    assert bytes(machine.cpu.mem_read(output + 0x1a8, 4)) == human[0x1a8:0x1ac]
    print('native writer and reader: 18 members, 9/9 teams, human fields preserved')


if __name__ == '__main__':
    verify(bytes.fromhex(sys.argv[1]), bytes.fromhex(sys.argv[2]))
