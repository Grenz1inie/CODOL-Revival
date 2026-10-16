"""3.3.3.3 messages, checked against client readers 0x46db20/0x46dea0.

Bit bytes are reserved at the current byte cursor. Ordinary fields append
without aligning the bit cursor (client MSG_ReadBit/MSG_ReadBits).
"""
import json
from pathlib import Path
import struct
import math

PLAYER_FIELDS = json.loads((Path(__file__).resolve().parents[5] /
                            'games/codol/versions/v3_3_3_3/resources/definitions/story-player-fields423.json').read_text())['fields']
MATCH_FIELDS = json.loads((Path(__file__).resolve().parents[5] /
                          'games/codol/versions/v3_3_3_3/resources/definitions/match-fields423.json').read_text())


def encode_packets(payload, *, sequence, acknowledgement, challenge, command=b''):
    """Native channel packets after the transport handshake (no DTLS wrapper)."""
    for name, value, maximum, minimum in (('sequence', sequence, 0x1fffffff, 1),
                                         ('acknowledgement', acknowledgement, 0x7fffffff, 0),
                                         ('challenge', challenge, 0xffffffff, 0)):
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f'{name} out of range')
    if not isinstance(payload, bytes) or not payload or len(payload) > 0x20000 - 8:
        raise ValueError('packet payload exceeds message buffer')
    if not isinstance(command, bytes) or b'\0' in command or len(command) > 1023:
        raise ValueError('command exceeds client ring entry')
    key = (challenge ^ sequence) & 255
    encrypted = bytearray(payload)
    for i in range(len(encrypted)):
        if command:
            key ^= (command[i % len(command)] << (i & 1)) & 255
        encrypted[i] ^= key
    message = struct.pack('<I', acknowledgement) + encrypted
    stride = 0x482
    if len(message) < stride:
        return [struct.pack('<I', sequence) + message]
    count = (len(message) + stride - 1) // stride
    return [struct.pack('<IBBHH', sequence | 0x80000000, index, count - 1,
                        stride, len(message[index * stride:(index + 1) * stride])) +
            message[index * stride:(index + 1) * stride] for index in range(count)]


class _Message:
    def __init__(self):
        self.data = bytearray()
        self.bit = 0

    def bits(self, value, width):
        for i in range(width):
            if self.bit % 8 == 0:
                self.bit = len(self.data) * 8
                self.data.append(0)
            self.data[self.bit // 8] |= ((value >> i) & 1) << (self.bit % 8)
            self.bit += 1

    def index(self, index, previous):
        self.bits(index == previous + 1, 1)
        if index != previous + 1:
            self.bits(index, 13)


def _player_value(message, bits, previous, value):
    if bits == -94:
        old_event, old_parameter = previous & 0xffffffff, previous >> 32
        event, parameter = value & 0xffffffff, value >> 32
        width = MATCH_FIELDS['event_widths'][event]
        message.bits(event != old_event, 1)
        if event != old_event:
            message.data.append(event)
            if not width:
                return
            changed = width == 32 or (old_parameter & ((1 << width)-1)) != parameter
            message.bits(changed, 1)
            if not changed:
                return
        if width == 32:
            message.data.extend(struct.pack('<I', parameter))
        else:
            message.bits(parameter, width)
    elif bits in (-87, -100):
        if bits == -100:
            message.bits(0, 2)
        angle = struct.unpack('<f', struct.pack('<I', value))[0]
        message.data.extend(struct.pack('<H', round(angle * 182.04444885253906) & 65535))
    elif bits == -98:
        message.bits(1, 1)
        message.bits(value, 30)
    elif bits in (-70, -97):
        message.bits(1, 1)  # Absolute time, independent of server-time delta.
        message.data.extend(struct.pack('<I', value))
    elif bits == -88:
        message.data.extend(struct.pack('<I', value ^ previous))
    elif bits == 0:
        message.bits(1, 1)
        message.bits(1, 1)  # Exact float word; avoid lossy integer quantization.
        message.data.extend(struct.pack('<I', value ^ previous))
    elif bits == -57:
        message.bits(value, 1)
    elif bits == -101:
        message.bits(value != previous, 1)
        if value != previous:
            message.bits(value, 6)
    else:
        if bits == -75:
            message.bits(0, 1)  # Full 8-bit XOR instead of increment shortcut.
            width = 8
        else:
            message.bits(value != 0, 1)
            if not value:
                return
            width = abs(bits)
        delta = (value ^ previous) & ((1 << width) - 1)
        remainder = width % 8
        message.bits(delta, remainder)
        for shift in range(remainder, width, 8):
            message.data.append((delta >> shift) & 255)


def _write_player_fields(message, values, base, server_time):
    if type(server_time) is not int or not 0 <= server_time <= 0xffffffff:
        raise ValueError('server time must be uint32')
    for state in (base, values):
        for index, value in state.items():
            if type(index) is not int or not 0 <= index < 235:
                raise ValueError('player field index out of range')
            bits = PLAYER_FIELDS[index][1]
            if type(value) is not int or not 0 <= value < 1 << (64 if bits == -94 else 32):
                raise ValueError('player field exceeds its word size')
            if bits == -94:
                event, parameter = value & 0xffffffff, value >> 32
                if event < len(MATCH_FIELDS['event_widths']) and parameter < 1 << MATCH_FIELDS['event_widths'][event]:
                    continue
            if bits in (-87, -100):
                if math.isfinite(struct.unpack('<f', struct.pack('<I', value))[0]):
                    continue
            if bits == -98 and value < 1 << 30:
                continue
            if bits in (-70, -97, -88, 0):
                continue
            if bits in (-75, -57, -101):
                limit = {-75: 255, -57: 1, -101: 63}[bits]
                if value <= limit:
                    continue
            elif 0 < bits <= 32 and value < 1 << bits:
                continue
            elif bits in (-8, -16) and (value < 1 << (-bits - 1) or
                                         value >= 0x100000000 - (1 << (-bits - 1))):
                continue
            elif value == 0:
                continue
            raise ValueError(f'player field {index}: unsupported codec or value out of range')
    selected = [i for i, (_, _, hint) in enumerate(PLAYER_FIELDS)
                if hint == 3 or values.get(i, 0) != base.get(i, 0)]
    last = selected[-1]
    message.bits(1, 1)
    message.bits(last + 1, 8)
    previous = -1
    for index in selected:
        _, bits, hint = PLAYER_FIELDS[index]
        if hint == 2 and index < last:
            continue
        gap = index - previous
        message.bits(gap == 1, 1)
        if gap != 1:
            gap -= 1
            while gap >= 15:
                message.bits(15, 4)
                gap -= 15
            message.bits(gap, 4)
        _player_value(message, bits, 0 if hint == 3 else base.get(index, 0), values.get(index, 0))
        previous = index
    for index in range(last):
        _, bits, hint = PLAYER_FIELDS[index]
        if hint == 2:
            _player_value(message, bits, base.get(index, 0), values.get(index, 0))


def _write_playerstate(message, values, base, server_time):
    _write_player_fields(message, values, base, server_time)
    message.bits(0, 14)  # 14 unchanged array sections in 0x5a4230.


def encode_playerstate(values, *, server_time, base=None):
    """Sparse complete states, keyed by current field index; unspecified = zero.

    Supports measured integer/time/float, view-angle and event-pair fields.
    Array sections remain unchanged; match_server.snapshot supplies inventory.
    """
    message = _Message()
    _write_playerstate(message, values, base or {}, server_time)
    message.data.append(6)
    return bytes(message.data)


def encode_snapshot(values, *, server_time):
    """Initial pinned snapshot with no dynamic actors/entities or array updates.

    This establishes the parsing boundary; it is not a simulated game world.
    """
    message = _Message()
    message.data.extend(b'\0' + struct.pack('<I', server_time) + b'\0\x08')
    message.bits(0, 1)  # No previous playerstate.
    _write_playerstate(message, values, {}, server_time)
    message.bits(0, 1)  # No animation commands.
    message.bits(0, 1)  # No actors.
    message.bits(0, 1)
    message.bits(1, 1)
    message.bits(2047, 11)  # Entity terminator, not an entity record.
    message.bits(0, 1)  # No client records.
    message.bits(0, 1)  # No glass updates.
    message.data.append(6)
    return bytes(message.data)


def encode_configstrings(ordinary, *, aliases=(), recipes=()):
    """Recipes: (index, weapon, camo, extra9, attachments).

    extra9 is the current client's third recipe field; its gameplay meaning
    remains unconfirmed, so the wire layer does not infer a cosmetic default.
    """
    if len(ordinary) > 7058 or len(aliases) > 1023 or len(recipes) > 1023:
        raise ValueError('configstring count out of range')
    used = set()
    for row in (*ordinary, *aliases, *recipes):
        index = row[0]
        if type(index) is not int or not 0 <= index < 7058:
            raise ValueError('configstring index out of range')
        if index in used:
            raise ValueError('duplicate configstring index')
        used.add(index)
    # Complement of the client's 0xc57118 NCS layout, plus runtime value kind 19.
    ordinary_ranges = ((0, 24), (344, 856), (1975, 2047), (6383, 6416), (6544, 7058))
    for index, text in ordinary:
        if not any(start <= index < end for start, end in ordinary_ranges):
            raise ValueError('ordinary string overwrites a registered resource')
        if (not isinstance(text, str) or '\0' in text or '%' in text or
                not text.isascii() or len(text) > 8191):
            raise ValueError('configstring string would be normalized or truncated')
    for _, weapon in aliases:
        if type(weapon) is not int or not 0 <= weapon < 1024:
            raise ValueError('weapon index out of range')
    for _, weapon, camo, extra9, attachments in recipes:
        for name, value, width in (('weapon', weapon, 10), ('camo', camo, 8), ('extra9', extra9, 9)):
            if type(value) is not int or not 0 <= value < (1 << width):
                raise ValueError(f'recipe {name} out of range')
        if len(attachments) > 15 or any(type(a) is not int or not 0 <= a < 16384 for a in attachments):
            raise ValueError('recipe attachment count or value out of range')
    pool_size = 1 + sum(len(text) + 1 for _, text in ordinary)
    pool_size += sum(len(f'* {weapon}') + 1 for _, weapon in aliases)
    pool_size += sum(len('** ' + ' '.join(map(str, (weapon, camo, extra9, *attachments)))) + 1
                     for _, weapon, camo, extra9, attachments in recipes)
    if pool_size > 0x20000:
        raise ValueError('configstring pool exceeds 128 KiB')
    message = _Message()
    message.data.extend(struct.pack('<h', len(ordinary)))
    previous = -1
    for index, text in ordinary:
        message.index(index, previous)
        message.data.extend(text.encode('ascii') + b'\0')
        previous = index
    message.bits(len(aliases), 10)
    previous = -1
    for index, weapon in aliases:
        message.index(index, previous)
        message.bits(weapon, 10)
        previous = index
    message.bits(len(recipes), 10)
    previous = -1
    for index, weapon, camo, extra9, attachments in recipes:
        message.index(index, previous)
        message.bits(weapon, 10)
        message.bits(camo, 8)
        message.bits(bool(extra9), 1)
        if extra9:
            message.bits(extra9, 9)
        message.bits(len(attachments), 4)
        for attachment in attachments:
            message.bits(attachment, 14)
        previous = index
    message.data.append(6)  # SVC_EOF terminates this configstring section.
    return bytes(message.data)


def encode_gamestate(map_name, category, netconst_checksum, *, command_sequence,
                     client_number, checksum_feed, ordinary, aliases=(), recipes=()):
    """Encode SVC_GAMESTATE, including its nested section and outer EOF.

    The client consumes these header names but selects the map using serverinfo
    in configstring 0. Callers must also provide that actual loading context.
    """
    for name in (map_name, category):
        if (not isinstance(name, str) or not 0 < len(name) < 32 or
                '\0' in name or '%' in name or not name.isascii()):
            raise ValueError('map and category must fit the client string buffers')
    for value in (command_sequence, netconst_checksum, checksum_feed):
        if type(value) is not int or not 0 <= value <= 0xffffffff:
            raise ValueError('gamestate field must be uint32')
    if type(client_number) is not int or not 0 <= client_number < 19:
        raise ValueError('client number must be in 0..18')
    configstrings = encode_configstrings(ordinary, aliases=aliases, recipes=recipes)
    wire = (b'\x03' + struct.pack('<I', command_sequence) + map_name.encode('ascii') + b'\0' +
            category.encode('ascii') + b'\0' + struct.pack('<I', netconst_checksum) +
            b'\x04' + configstrings + struct.pack('<II', client_number, checksum_feed) + b'\x06')
    if len(wire) > 0x20000:  # Outer client dispatcher 0x46e6a0.
        raise ValueError('gamestate message exceeds 128 KiB')
    return wire
