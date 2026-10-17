"""Emit the hash-bound experimental Ready gate; no process access or file writes."""
import struct

ORIGINAL = bytes.fromhex('558bec83ec08')


def gate(base, cave):
    code = bytearray(b'\x9c\x50\xa1' + struct.pack('<I', base + 0x7ee13fc))
    branches = []
    def condition(opcode):
        branches.append(len(code) + 1)
        code.extend([opcode, 0])
    code.extend(b'\x85\xc0') # Null room: keep original behavior.
    condition(0x74)
    code.extend(b'\x80\xb8' + struct.pack('<I', 0x281) + b'\1')
    condition(0x75) # Only the local-host room, never a remote room.
    code.extend(b'\x80\xb8' + struct.pack('<I', 0x105fc) + b'\x19') # Playlist110 -> native25.
    condition(0x75)
    code.extend(b'\x81\xb8' + struct.pack('<II', 0xe368, 1000001))
    condition(0x75)
    code.extend(b'\x83\xb8' + struct.pack('<I', 0xe36c) + b'\0')
    condition(0x75)
    code.extend(b'\x83\x79\x20\x01')
    condition(0x72) # Preserve initialization before the waiting states.
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
    code.extend(b'\xe9' + struct.pack('<I', (entry + 6 - (cave + len(code) + 5)) & 0xffffffff))
    return bytes(code), b'\xe9' + struct.pack('<I', (cave - entry - 5) & 0xffffffff) + b'\x90'
