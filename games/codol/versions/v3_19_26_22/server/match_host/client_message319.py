"""3.19 client sequenced-message reader (writer traced at 005B2C10).

Datagram: u32 netchan sequence, then the 9-byte message header
  u8 serverId (client+3BE8), u32 server sequence ack (conn+80148),
  u32 server command ack (conn+8014C);
then a payload transformed by 004709E0 (key starts at the header's
serverAck ^ serverId ^ challenge, mixed with the last server command text).
Payload, using the native independent byte cursor / bit cursor:
  repeated 3-bit op:
    2 clientCommand: raw u32 command number, NUL-terminated string
    0 move (delta) / 1 moveNoDelta: u8 count, then keyed usercmd deltas (0066F410)
    3 EOF
Usercmd deltas are not decoded here yet; parsing stops at a move op.
"""
import math
import struct

HEADER = struct.Struct('<IBII')
OP_MOVE, OP_MOVE_NODELTA, OP_COMMAND, OP_EOF = 0, 1, 2, 3


class Cursor:
    """Native-equivalent reader: whole bytes and bit groups advance independently."""
    def __init__(self, data):
        self.data = data; self.read = 0; self.bit = 0; self.error = False

    def bits(self, width):
        value = 0
        for i in range(width):
            if not self.bit & 7:
                if self.read >= len(self.data):
                    self.error = True; return 0
                self.bit = self.read * 8; self.read += 1
            value |= ((self.data[self.bit // 8] >> (self.bit & 7)) & 1) << i
            self.bit += 1
        return value

    def u32(self):
        if len(self.data) - self.read < 4:
            self.error = True; return 0
        value = struct.unpack_from('<I', self.data, self.read)[0]; self.read += 4
        return value

    def u16(self):
        if len(self.data) - self.read < 2:
            self.error = True; return 0
        value = struct.unpack_from('<H', self.data, self.read)[0]; self.read += 2
        return value

    def byte(self):
        if self.read >= len(self.data):
            self.error = True; return 0
        value = self.data[self.read]; self.read += 1
        return value

    def string(self, limit=1024):
        end = self.data.find(b'\0', self.read, self.read + limit)
        if end < 0:
            self.error = True; return b''
        value = self.data[self.read:end]; self.read = end + 1
        return value


def payload_key(server_ack, server_id, challenge):
    return (server_ack ^ server_id ^ challenge) & 0xff


def command_hash(command):
    """00769560: over at most 32 chars (stop at NUL) h += signed char * (119 + i);
    t = (h >> 10) ^ h; result = (t >> 10) ^ h (arithmetic shifts, 32-bit)."""
    h = 0
    for i, ch in enumerate(bytes(command)[:32]):
        if ch == 0:
            break
        h = (h + (ch - 256 if ch > 127 else ch) * (119 + i)) & 0xffffffff
    sh = h - (1 << 32) if h & 0x80000000 else h
    t = ((sh >> 10) ^ sh) & 0xffffffff
    st = t - (1 << 32) if t & 0x80000000 else t
    return ((st >> 10) ^ sh) & 0xffffffff


def decode_payload(payload, key, last_server_command=b''):
    """Inverse of 004709E0 for the client direction (same mixing as server_message319)."""
    command = bytes(last_server_command).split(b'\0', 1)[0] + b'\0'
    out = bytearray(payload); cursor = 0
    for i in range(len(out)):
        if command[cursor] == 0:
            cursor = 0
        key ^= (command[cursor] << (i & 1)) & 0xff
        cursor += 1
        if len(command) == 1:
            cursor = 0
        out[i] ^= key
    return bytes(out)


FORWARD, BACK, RIGHT, LEFT = 1, 2, 4, 8   # move class bits (0066F49E: >10 / <-10)


def _changed(c):
    return c.bits(1)


def read_usercmd(c, key, old):
    """Inverse of the native writer 0066F410 (usercmd 0x2C bytes at client+3CD0).

    key: hash(last server command) ^ serverMessageSequence ^ checksumFeed; with no
    server commands and checksumFeed 0 it is the packet's server ack (005B2EAB).
    old/new: dict(server_time, buttons, angles[3], move_class, w14, w16, w18, extra).
    Returns the new dict; raises ValueError on a malformed command.
    """
    new = dict(old); new['angles'] = list(old['angles']); new['extra'] = dict(old['extra'])
    if c.bits(1):
        new['server_time'] = (old['server_time'] + c.byte()) & 0xffffffff
    else:
        new['server_time'] = c.u32()
    kbit = key & 1
    def angle(i, k):
        if _changed(c):
            new['angles'][i] = (c.u16() ^ k) & 0xffff
    def field(name, width, k):
        if _changed(c):
            new[name] = (c.bits(width) ^ k) & ((1 << width) - 1)
    def byte_field(name, k):
        if _changed(c):
            new['extra'][name] = (c.byte() ^ k) & 0xff
    if (c.bits(1) ^ kbit) == 0:                      # case A: unchanged
        if c.bits(3) != 7:
            raise ValueError('usercmd case A terminator')
        return new
    if (c.bits(1) ^ kbit) == 0:                      # case B (0066F5D5)
        k = (key ^ new['server_time']) & 0xffffffff
        new['buttons'] = (old['buttons'] & ~1) | ((c.bits(1) ^ k) & 1)
        angle(0, k); angle(1, k); field('move_class', 4, k)
        if c.bits(3) != 2:
            raise ValueError('usercmd case B terminator')
        return new
    k = key                                          # case C (0066F656)
    bit0 = (c.bits(1) ^ k) & 1
    angle(0, k); angle(1, k); field('move_class', 4, k)
    k = (key ^ new['server_time']) & 0xffffffff
    angle(2, k)
    high = old['buttons'] >> 1
    if _changed(c):
        high = (c.bits(29) ^ k) & 0x1fffffff
    new['buttons'] = (high << 1) | bit0
    field('w14', 11, k); field('w18', 11, k); field('w16', 11, k)
    if new['buttons'] & 0x20000:
        byte_field('b24', k); byte_field('b25', k); byte_field('b26', k)
    if new['buttons'] & 0x200000:
        byte_field('b27', k); byte_field('b28', k)
    if new['buttons'] & 4:
        if _changed(c):
            new['extra']['a1c'] = (c.u16() ^ k) & 0xffff
        field('b20', 8, k); field('w22', 11, k)
    if c.bits(3) != 5:
        raise ValueError('usercmd case C terminator')
    return new


def null_usercmd():
    return dict(server_time=0, buttons=0, angles=[0, 0, 0], move_class=0,
                w14=0, w16=0, w18=0, b20=0, w22=0, extra={})


def short_to_degrees(value):
    value &= 0xffff
    return (value - 0x10000 if value >= 0x8000 else value) * 360.0 / 65536.0


def parse(packet, challenge=0, last_server_command=b'', baseline=None):
    """Return dict(header..., commands=[(number, text)], move=None|dict) or None.

    baseline: last usercmd decoded from this client's previous packet. Delta moves
    (OP_MOVE) chain the first command from it: each packet repeats the previous
    packet's newest command first, and an unchanged command is written as case A,
    which decoded from a zeroed command gave yaw/pitch 0 and no movement keys
    (30% of commands in run 073938Z while the mouse was still). OP_MOVE_NODELTA,
    or no baseline, starts from a zeroed command.
    """
    if len(packet) < HEADER.size:
        return None
    sequence, server_id, server_ack, command_ack = HEADER.unpack_from(packet)
    plain = decode_payload(packet[HEADER.size:], payload_key(server_ack, server_id, challenge),
                           last_server_command)
    c = Cursor(plain); commands = []; move = None; eof = False
    while not c.error:
        op = c.bits(3)
        if c.error:
            break
        if op == OP_COMMAND:
            number = c.u32(); text = c.string()
            if c.error:
                break
            commands.append((number, text.decode('latin-1')))
        elif op in (OP_MOVE, OP_MOVE_NODELTA):
            move = dict(delta=op == OP_MOVE, count=c.byte(), offset=c.read, cmds=[])
            if True:
                # 005B2E96: key = hash(serverCommands[serverCommandSequence]) ^ serverMessageSequence
                # ^ checksumFeed (0 here); the hash term is 0 before any server command.
                key = (server_ack ^ (command_hash(last_server_command) if last_server_command else 0)) & 0xffffffff
                old = baseline if (baseline is not None and op == OP_MOVE) else null_usercmd()
                try:
                    for _ in range(move['count']):
                        old = read_usercmd(c, key, old)
                        if c.error:
                            raise ValueError('truncated usercmd')
                        move['cmds'].append(old)
                except ValueError as ex:
                    move['cmd_error'] = str(ex)
                # Client predicted origin (3 floats) and its command time, as the
                # IW CL_WritePacket appends them (1.1.1.13 SV_UserMove reads the same
                # four longs; run 074913Z: time == the last command's serverTime).
                if 'cmd_error' not in move:
                    raw = [c.u32() for _ in range(4)]
                    if not c.error:
                        xyz = [struct.unpack('<f', struct.pack('<I', v))[0] for v in raw[:3]]
                        if all(math.isfinite(v) and abs(v) < 131072 for v in xyz):
                            move['predicted'] = (xyz, raw[3])
            break
        elif op == OP_EOF:
            eof = True
            break
        else:
            c.error = True
    return dict(sequence=sequence, server_id=server_id, server_ack=server_ack,
                command_ack=command_ack, commands=commands, move=move, eof=eof,
                error=c.error, plain=plain)
