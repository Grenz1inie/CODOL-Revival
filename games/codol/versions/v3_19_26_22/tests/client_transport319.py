"""Hash-bound native UDP contracts, executed offline in Unicorn."""
import json
import struct
import sys
import zlib
from client_inventory319 import InventoryReader319
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESI


def server_packets(cases):
    machine = InventoryReader319()
    cpu, obj = machine.cpu, machine.object
    cpu.mem_map(0x331c000, 0x1000)
    machine.write32(0x331c0c8, obj ^ 0xd362501f)
    for case in cases:
        packet, plain, command = (bytes(case[key]) for key in ('packet', 'plain', 'command'))
        sequence, ack = struct.unpack_from('<II', packet)
        machine.write32(obj + 0x144, ack)
        machine.write32(obj + 0x80148, sequence)
        machine.write32(obj + 0x138, case['challenge'])
        cpu.mem_write(obj + 0x148 + (ack & 0x1ff) * 1024, command + bytes(1024 - len(command)))
        cpu.mem_write(machine.data, packet[8:])
        machine.call(0x470a60, 0, machine.data, len(packet) - 8)
        assert bytes(cpu.mem_read(machine.data, len(packet) - 8)) == plain
    return {'decoded': len(cases)}


def stats_fragments():
    machine = InventoryReader319()
    cpu, obj = machine.cpu, machine.object
    cpu.mem_map(0xc7af000, 0x1000)
    machine.write32(0xc7af6a8, 123)
    profile = bytes(i % 251 for i in range(32768))
    cpu.mem_write(obj + 0x8c, profile)
    compressed = zlib.compress(profile)
    cpu.mem_write(machine.data + 0x10000, compressed)
    result = []
    for length in (0, len(compressed)):
        frames = []
        for index in range(((length or 32768) + 0x4d5) // 0x4d6):
            machine.write32(obj + 0x84, 4)
            machine.write32(obj + 0x11098, machine.data + 0x10000)
            machine.write32(obj + 0x1109c, length)
            machine.write32(obj + 0x110b0, 1 << index)
            cpu.mem_write(obj + 0x110b4, bytes(0x6c))
            cpu.mem_write(machine.buffer, struct.pack('<6I', 0, 0, machine.data, 0, 4096, 0))
            cpu.reg_write(UC_X86_REG_EAX, obj)
            cpu.reg_write(UC_X86_REG_ESI, machine.buffer)
            machine.call(0x7f6ec0, 0)
            assert machine.u32(machine.buffer) == 0
            frames.append(list(cpu.mem_read(machine.data, machine.u32(machine.buffer + 20))))
        result.append(frames)
    return result


if __name__ == '__main__':
    request = json.load(sys.stdin)
    print(json.dumps(stats_fragments() if request == 'stats' else server_packets(request)))
