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
        assert bytes(machine.cpu.mem_read(row + 0x90, 1)) == (human[0x90:0x91] if slot == 0 else b'\0')
        # Names are populated by channel membership, not this room message.
        assert bytes(machine.cpu.mem_read(row + 8, 1)) == b'\0'
    assert bytes(machine.cpu.mem_read(output + 0x94, 4)) == human[0x94:0x98]
    assert bytes(machine.cpu.mem_read(output + 0x1a8, 4)) == human[0x1a8:0x1ac]
    print('native writer and reader: 18 members, 9/9 teams, human fields preserved')
    verify_countdown(machine, output)


def verify_joins(human, messages):
    machine = InventoryReader319()
    reference, string, output = 0x2001f000, 0x2001e000, 0x20005000
    machine.cpu.mem_write(string, struct.pack('<III', 1, 0, 1) + b'\0')
    machine.write32(reference, machine.buffer)
    assert len(messages) == 17
    for slot, payload in enumerate(messages, 1):
        row = bytearray(human)
        row[:8] = struct.pack('<Q', 0x600000000 + slot)
        row[0x88:0x8c] = struct.pack('<I', 1 if slot < 9 else 2)
        row[0x90] = 0
        row[0x48:0x88] = bytes(64)
        machine.cpu.mem_write(machine.object, bytes(0x1f4))
        machine.cpu.mem_write(machine.object, struct.pack('<4I', 0xdc75a0, 6, 1, string + 12))
        machine.cpu.mem_write(machine.object + 0x10, bytes(row))
        machine.cpu.mem_write(machine.object + 0x1e0, human[0x94:0x96])
        machine.write32(machine.object + 0x1e4, 797)
        machine.call(0xb778e0, machine.buffer, 0x1000, 0)
        machine.call(0x6270d0, machine.object, reference)
        native = bytes(machine.cpu.mem_read(machine.u32(machine.buffer + 8), machine.u32(machine.buffer + 0x10)))
        assert payload == native, 'Rust join differs from native writer 0x6270d0'
        machine.cpu.mem_write(machine.data, payload)
        machine.call(0xb779a0, machine.buffer, machine.data, len(payload) * 8, 1)
        machine.call(0x623770, output + 0x10)
        machine.write32(output + 0xc, string + 12)
        assert machine.call(0x627230, output, reference) == 1
        assert machine.u32(machine.buffer + 0x1c) == 722
        assert machine.u32(output + 4) == 6 and machine.u32(output + 8) == 1
        assert bytes(machine.cpu.mem_read(output + 0x10, 8)) == row[:8]
        assert machine.u32(output + 0x98) == (1 if slot < 9 else 2)
        assert bytes(machine.cpu.mem_read(output + 0xa0, 1)) == b'\0'
        assert bytes(machine.cpu.mem_read(output + 0x1c0, 1)) == human[0x1b0:0x1b1]
        assert machine.u32(output + 0x1e4) == 797
        assert machine.logs == 0
    print('native join writer and reader: all 17 bot identities and teams')


def verify_countdown(machine, rows):
    """Execute native readiness decisions, stubbing only clock/environment/actions."""
    from unicorn import UC_HOOK_CODE
    from unicorn.x86_const import UC_X86_REG_EDI, UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP
    cpu, room = machine.cpu, machine.object
    members = bytes(cpu.mem_read(rows, 18 * 0x1d0))
    cpu.mem_write(room, bytes(0x10800))
    cpu.mem_write(room + 0xe368, members)
    cpu.mem_write(room + 0x281, b'\1')
    cpu.mem_write(room + 0x105fd, b'\x12')
    machine.write32(room + 0x105d8, 18)
    machine.write32(room, 0x20050000)
    for offset, target in ((0x54, 0xf00300), (0x5c, 0xf00300), (0x64, 0x62fe80),
                           (0x3c, 0xf00310), (0x40, 0xf00320), (0x48, 0xf00330)):
        machine.write32(0x20050000 + offset, target)
    for address in (0x849b000, 0x7644000):
        cpu.mem_map(address, 0x1000)
    machine.write32(0x849b7a8, 0x20052000)
    machine.write32(0x849b7ac, 0x20052100)
    cpu.mem_write(0x2005200c, struct.pack('<f', 60))
    cpu.mem_write(0x2005210c, struct.pack('<f', 5))
    # Test clock result on x87 ST(0); no live client or real timer is modified.
    cpu.mem_write(0xf00400, b'\xdd\x05' + struct.pack('<I', 0x20051000) + b'\xc3')
    actions = []
    elapsed = 0.0

    def hook(cpu, address, size, _):
        nonlocal elapsed
        if address == 0xb75da0:
            cpu.mem_write(0x20051000, struct.pack('<d', elapsed))
            cpu.reg_write(UC_X86_REG_EIP, 0xf00400)
            return
        if address in (0xf00310, 0xf00320, 0xf00330):
            actions.append({0xf00310: 'start', 0xf00320: 'countdown', 0xf00330: 'cancel'}[address])
            elapsed = 0.01 if address == 0xf00320 else 0.0
        cpu.reg_write(UC_X86_REG_EAX, int(address in (0xf00300, 0x775ad0)))
        sp = cpu.reg_read(UC_X86_REG_ESP)
        cpu.reg_write(UC_X86_REG_ESP, sp + (16 if address == 0xf00310 else 4))
        cpu.reg_write(UC_X86_REG_EIP, machine.u32(sp))

    for address in (0xf00300, 0xf00310, 0xf00320, 0xf00330, 0xb75da0, 0xc74510, 0x775ad0):
        cpu.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)
    def tick():
        cpu.reg_write(UC_X86_REG_EDI, room)
        machine.call(0x632a70, room)
    tick()
    tick()
    assert actions == [], 'Entering a full room must not start a countdown'
    cpu.mem_write(room + 0xe3f8, b'\1') # Human Ready; bots remain unready.
    tick()
    tick()
    assert actions == ['countdown'], 'Human Ready starts exactly one countdown'
    elapsed = 60.0
    tick()
    assert actions == ['countdown', 'start'], 'Countdown expiry starts the room'
    print('native 0x632a70: idle without Ready, one countdown after Ready, start at expiry')


if __name__ == '__main__':
    if sys.argv[1] == 'join':
        verify_joins(bytes.fromhex(sys.argv[2]), [bytes.fromhex(value) for value in sys.argv[3:]])
    else:
        verify(bytes.fromhex(sys.argv[1]), bytes.fromhex(sys.argv[2]))
