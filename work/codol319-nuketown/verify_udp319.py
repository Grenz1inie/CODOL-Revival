"""Offline native transport proof; original 3.19 snapshots only."""
from pathlib import Path
import struct
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'games/codol/versions/v3_19_26_22/tests'))
from client_inventory319 import InventoryReader319
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ESI

m = InventoryReader319()
m.cpu.mem_map(0x331c000, 0x1000)
m.write32(0x331c0c8, m.object ^ 0xd362501f)
plain = bytes(range(256)) * 4
for command in (b'', b'gamestateupdate 6', b'abc', b'x\x80\xff'):
    m.cpu.mem_write(m.object + 0x148, command + bytes(1024 - len(command)))
    m.write32(m.object + 0x144, 0)
    m.write32(m.object + 0x80148, 1234)
    m.write32(m.object + 0x138, 123456)
    m.cpu.mem_write(m.data, plain)
    m.call(0x470a60, 0, m.data, len(plain))
    expected, key = bytearray(plain), (1234 ^ 123456) & 255
    for i in range(len(expected)):
        key ^= ((command[i % len(command)] if command else 0) << (i & 1)) & 255
        expected[i] ^= key
    assert bytes(m.cpu.mem_read(m.data, len(plain))) == expected
    m.call(0x470a60, 0, m.data, len(plain))
    assert bytes(m.cpu.mem_read(m.data, len(plain))) == plain
print('native 0x470a60: XOR validated for empty, repeated, non-ASCII command bytes')

m.cpu.mem_map(0xc7af000, 0x1000)
m.write32(0xc7af6a8, 123)
profile = bytes(i % 251 for i in range(32768))
m.cpu.mem_write(m.object + 0x8c, profile)
compressed = __import__('zlib').compress(profile)
m.cpu.mem_write(m.data + 0x10000, compressed)
for length in (0, len(compressed)):
    source = profile if length == 0 else compressed
    for index in range((len(source) + 0x4d5) // 0x4d6):
        m.write32(m.object + 0x84, 4)
        m.write32(m.object + 0x11098, m.data + 0x10000)
        m.write32(m.object + 0x1109c, length)
        m.write32(m.object + 0x110b0, 1 << index)
        m.cpu.mem_write(m.object + 0x110b4, bytes(0x6c))
        # Native msg_t: overflow, readOnly, data, splitData, maxSize, curSize.
        m.cpu.mem_write(m.buffer, struct.pack('<6I', 0, 0, m.data, 0, 4096, 0))
        m.cpu.reg_write(UC_X86_REG_EAX, m.object)
        m.cpu.reg_write(UC_X86_REG_ESI, m.buffer)
        m.call(0x7f6ec0, 0)
        expected = bytes([index]) + struct.pack('<H', length) + source[index*0x4d6:(index+1)*0x4d6]
        assert m.u32(m.buffer) == 0
        assert m.u32(m.buffer + 20) == len(expected)
        assert bytes(m.cpu.mem_read(m.data, len(expected))) == expected
print('native 0x7f6ec0: all 27 raw fragments and compressed fragment match')
