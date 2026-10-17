"""Replay the 3.19 client XOR function before implementing Rust decoding."""
from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
VERSION = ROOT/'games/codol/versions/v3_19_26_22'
sys.path[:0] = [str(VERSION/'tests'), str(VERSION/'server/match_host')]
from client_inventory319 import InventoryReader319
from client_message319 import decode_payload, parse
from unicorn.x86_const import UC_X86_REG_EDX

machine = InventoryReader319()
cpu, obj = machine.cpu, machine.object
cpu.mem_map(0x331c000, 0x1000)
cpu.mem_map(0xc86d000, 0x1000)
machine.write32(0x331c0c8, obj ^ 0xd362501f)
log = Path('A:/CODOL-Lab/ready319-20261017/matches/1792206595588129900/logs/match.log')
packets = [bytes(row['data']) for line in log.read_text().splitlines()
           if (row := json.loads(line))['event'] == 'received' and len(row['data']) > 13
           and row['data'][:4] != [255]*4]
results = []
for packet in (packets[0], packets[4], packets[-1]):
    sequence, server_id, ack, command_ack = struct.unpack_from('<IBII', packet)
    assert command_ack == 0
    machine.write32(obj+0x80148, ack)
    machine.write32(obj+0x8014c, command_ack)
    machine.write32(obj+0x138, 0)
    machine.write32(0xc86dd24, server_id)
    cpu.mem_write(obj+0x80154, bytes(1024))
    cpu.mem_write(machine.data, packet[13:])
    cpu.reg_write(UC_X86_REG_EDX, machine.data)
    machine.call(0x4709e0, 0, len(packet)-13)
    plain = bytes(cpu.mem_read(machine.data, len(packet)-13))
    assert plain == decode_payload(packet[13:], ack ^ server_id)
    results.append({'sequence': sequence, 'packet_hex': packet.hex(), 'plain_hex': plain.hex(),
                    'decoded': parse(packet)})
result = {'version': '3.19.26.22', 'exe_sha256': '36997674b18f2896de5e9d755686f6922af10708f355175714058d0a0172b537',
          'address': '0x4709e0', 'source': 'saved native text in Unicorn, actual loopback UDP packet bytes',
          'coverage': 'empty reliable server-command history; headers, initial and repeated reliable commands',
          'unverified': 'nonempty server-command history and live Rust consumption', 'cases': results}
serialized = json.dumps(result, indent=2, default=lambda value: value.hex())
(Path(__file__).parent/'client-crypto.json').write_text(serialized)
print(serialized)
