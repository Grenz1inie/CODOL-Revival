"""3.19 snapshot writer. Field layouts are verified against the original client.

The wire interleaves LSB bit fields with unaligned raw byte writes. A raw write
does not flush the partly filled bit byte. See snapshot319-reference.json.
"""
import json
import math
from pathlib import Path
import struct


DEFINITION = json.loads(Path(__file__).with_name('snapshot_fields319.json').read_text())
PLAYER = DEFINITION['player']
CLIENT = DEFINITION['client']
ENTITY = DEFINITION['entity']
EVENT_WIDTHS = DEFINITION['event_widths']


def word(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def floating(value):
    return struct.unpack('<f', struct.pack('<I', value))[0]


def bounded(value, low, high):
    if not low <= value <= high:
        raise ValueError('3.19 snapshot value out of range')
    return value


class Message:
    def __init__(self):
        self.data = bytearray()
        self.cursor = 0

    def raw(self, value, size=1):
        self.data.extend(value.to_bytes(size, 'little'))

    def bits(self, value, width):
        if width == 32:
            self.raw(value, 4)
            return
        for bit in range(width):
            if self.cursor % 8 == 0:
                self.cursor = len(self.data) * 8
                self.data.append(0)
            self.data[self.cursor // 8] |= ((value >> bit) & 1) << (self.cursor % 8)
            self.cursor += 1

    def compressed(self, value, width):
        tail = width % 8
        self.bits(value, tail)
        for shift in range(tail, width, 8):
            self.raw((value >> shift) & 255)


def event(message, event_id, parameter):
    bounded(event_id, 0, len(EVENT_WIDTHS) - 1)
    width = EVENT_WIDTHS[event_id]
    bounded(parameter, 0, (1 << width) - 1)
    message.bits(int(event_id != 0), 1)
    if event_id:
        message.raw(event_id)
        if width:
            message.bits(1, 1)
    if width:
        message.bits(parameter, width)


def delta(message, bits, value, stamp, parameter=0, event_id=0):
    """Encode against the zero baseline used by the live host."""
    if bits == -94:
        event(message, value, parameter)
        return
    if parameter:
        raise ValueError('Event parameter on a scalar field')
    if bits == -93:
        width = EVENT_WIDTHS[bounded(event_id, 0, len(EVENT_WIDTHS) - 1)]
        bounded(value, 0, (1 << width) - 1)
        if width:
            message.bits(value, width)
        return
    if -64 <= bits <= -62:
        bits = 0
    elif -61 <= bits <= -59:
        bits = -88
    elif bits == -79:
        bits = -100
    if -83 <= bits <= -81 or -92 <= bits <= -90:
        position = floating(value)
        if not math.isfinite(position):
            raise ValueError('Nonfinite entity position')
        rounded = bounded(round(position + 2**-30), -32768, 32767)
        message.bits(1, 1)
        message.bits((rounded + 32768) ^ 32768, 16)
    elif 1 <= abs(bits) <= 32:
        signed = value if value < 0x80000000 else value - 0x100000000
        if bits < 0:
            bounded(signed, -(1 << (-bits - 1)), (1 << (-bits - 1)) - 1)
        else:
            bounded(value, 0, (1 << bits) - 1)
        message.bits(int(value != 0), 1)
        if value:
            message.compressed(value & ((1 << abs(bits)) - 1), abs(bits))
    elif bits == 0:
        if value & 0x7fffffff == 0:
            message.bits(0, 1)
            message.bits(value >> 31, 1)
        else:
            message.bits(3, 2)
            message.raw(value, 4)
    elif bits in (-87, -100):
        angle = floating(value)
        if not math.isfinite(angle):
            raise ValueError('Nonfinite angle')
        encoded = round(floating(word(angle * 182.04444885253906))) % 65536
        if bits == -100:
            message.bits(0, 2)
        message.raw(encoded, 2)
    elif bits == -98:
        bounded(value, 0, 0x3fffffff)
        single = value != 0 and value & (value - 1) == 0
        message.bits(int(not single), 1)
        message.bits(value.bit_length() - 1 if single else value, 5 if single else 30)
    elif bits in (-97, -74, -72, -70):
        short = 0 <= stamp - value < 256
        message.bits(int(not short), 1)
        message.bits(stamp - value if short else value, 8 if short else 32)
    elif bits == -96:
        bounded(value, 0, 2047)
        message.bits(int(value == 2046), 1)
        if value != 2046:
            message.bits(int(value == 0), 1)
            if value:
                message.bits(value, 3)
                message.raw(value >> 3)
    elif bits in (-88, -80, -78, -73, -71):
        message.raw(value, 4)
    elif bits == -84:
        message.bits(bounded(value, 0, 127), 7)
    elif bits == -77:
        message.raw(bounded(value, 0, 255))
    elif bits == -76:
        signed = value if value < 0x80000000 else value - 0x100000000
        bounded(signed, -128, 127)
        short = -16 <= signed <= 15
        message.bits(int(short), 1)
        if short:
            message.bits(signed + 16, 5)
        else:
            message.raw(value & 255)
    elif bits == -75:
        bounded(value, 0, 255)
        message.bits(int(1 <= value <= 8), 1)
        if 1 <= value <= 8:
            message.bits(value - 1, 3)
        else:
            message.raw(value)
    elif bits == -57:
        message.bits(bounded(value, 0, 1), 1)
    elif bits == -56:
        for component in (value & 65535, value >> 16):
            bounded(component, 0, 1023)
            message.bits(int(component != 0), 1)
            if component:
                message.bits(component, 10)
    elif bits == -55:
        bounded(value, 0, 0xfffffff)
        for mask, parts in [(0x1ffff, [(0, 17)]), (0x47e0000, [(22, 1), (17, 5), (26, 1)]),
                            (0x8000000, [(27, 1)]), (0x3800000, [(23, 3)])]:
            message.bits(int(bool(value & mask)), 1)
            if value & mask:
                for shift, width in parts:
                    message.bits(value >> shift, width)
    elif bits == -102:
        bounded(value, 0, 0x7fffffff)
        message.bits(int(value != 0), 1)
        if value:
            message.bits(value, 31)
    elif bits == -101 and value == 0:
        message.bits(0, 1)
    else:
        raise ValueError(f'Unsupported 3.19 field codec/value: {bits}/{value}')


def gap(message, distance, width):
    message.bits(int(distance == 1), 1)
    if distance != 1:
        remaining = distance - 1
        maximum = (1 << width) - 1
        while remaining >= maximum:
            message.bits(maximum, width)
            remaining -= maximum
        message.bits(remaining, width)


def player(message, values, stamp):
    selected = [i for i, row in enumerate(PLAYER) if values[i] or row[2] == 3]
    last = selected[-1] + 1 if selected else 0
    message.bits(1, 1)
    message.bits(last, 8)
    previous = -1
    for i in selected:
        if PLAYER[i][2] == 2 and i < last - 1:
            continue
        gap(message, i - previous, 4)
        delta(message, PLAYER[i][1], values[i] & 0xffffffff, stamp, values[i] >> 32)
        previous = i
    for i in range(last - 1):
        if PLAYER[i][2] == 2:
            delta(message, PLAYER[i][1], values[i], stamp)


def entity_index(message, previous, number):
    bounded(number, previous + 1, 2047)
    distance = number - previous
    message.bits(int(distance == 1), 1)
    if distance != 1:
        large = distance > 511
        message.bits(int(large), 1)
        message.bits(number if large else distance, 11 if large else 9)


def entity(message, number, fields, mask, stamp):
    x, y, z, yaw = (word(float(v)) for v in fields[:4])
    attributes = [0, 0, 0, 1]
    attributes[:len(fields[4:])] = [int(v) for v in fields[4:]]
    weapon, legs, torso, kind = attributes
    bounded(kind, 0, 23)
    by_offset = {24: x, 28: y, 32: z}
    if mask & 1:
        by_offset.update({12: 1, 48: 1})
    if mask & 2:
        by_offset[64] = yaw
    if mask & 4 and kind == 1:
        by_offset[160] = number
    if mask & 8:
        by_offset.update({216: weapon, 220: legs, 224: torso})
    if mask & 16:
        by_offset[140] = 2046
    table = ENTITY[kind]
    values = [by_offset.get(row[0], 0) for row in table]
    selected = [i for i in range(1, 63) if kind or values[i] or -64 <= table[i][1] <= -62]
    last = selected[-1] if selected else 0
    message.bits(0, 1)
    message.bits(1, 1)
    message.bits(int(kind == 0), 1)
    message.bits(last, 6)
    message.bits(1, 1)
    message.raw(kind)
    previous = 0
    for i in selected:
        if table[i][2] == 2 and i < last:
            continue
        gap(message, i - previous, 3)
        delta(message, table[i][1], values[i], stamp, event_id=max(0, kind - 23))
        previous = i
    for i in range(1, last):
        if table[i][2] == 2:
            delta(message, table[i][1], values[i], stamp, event_id=max(0, kind - 23))


def encode(request, weapon=0, viewmodels=(0, 0), weapflags=0):
    tokens = request.split()
    if len(tokens) < 10:
        raise ValueError('Incomplete 3.19 snapshot request')
    stamp = bounded(int(tokens[0]), 1, 0x7fffffff)
    command = bounded(int(tokens[1]), 0, 0x7fffffff)
    floats = [float(v) for v in tokens[2:10]]
    for value in floats:
        bounded(value, -131072, 131072)
    flags, ground = 0, 2047
    extras = tokens[10:]
    if extras and '=' not in extras[0]:
        flags = int(extras.pop(0))
    if extras and '=' not in extras[0]:
        ground = bounded(int(extras.pop(0)), 0, 2047)
    values = [0] * len(PLAYER)
    values[0] = command
    for index, value in zip((8, 11, 10, 14, 13, 16, 19, 18), floats):
        values[index] = word(value)
    for index, _, value in DEFINITION['living']:
        values[index] = value
    for index, value in [(39, weapon), (57, viewmodels[0]), (118, viewmodels[1]),
                         (77, weapflags), (28, flags), (47, ground)]:
        values[index] = value
    clip, ammo, base_weapon = 30, 90, 0
    entities, clients, mask = [], [], 31
    for token in extras:
        name, value = token.split('=', 1)
        if name.startswith('F'):
            index = int(name[1:])
            parts = value.split(':')
            low = bounded(int(parts[0], 0), 0, 0xffffffff)
            high = bounded(int(parts[1], 0), 0, 0xffffffff) if len(parts) == 2 else 0
            if index == 900:
                clip = bounded(low, 0, 511)
            elif index == 901:
                ammo = bounded(low, 0, 4095)
            elif index == 902:
                base_weapon = bounded(low, 0, 2046)
            elif index in DEFINITION['allowed']:
                values[index] = low | (high << 32)
            else:
                raise ValueError('Unknown 3.19 snapshot override')
        elif name == 'BM':
            mask = int(value, 0)
        elif name.startswith('E'):
            entities.append((bounded(int(name[1:]), 1, 2045), value.split(',')))
        elif name.startswith('C'):
            clients.append((bounded(int(name[1:]), 0, 31), [int(v) for v in value.split(',')]))
        else:
            raise ValueError('Unknown 3.19 snapshot token')
    message = Message()
    message.raw(0)
    message.raw(stamp, 4)
    message.raw(0)
    message.raw(8)
    message.bits(0, 1)
    player(message, values, stamp)
    message.bits(1, 1)  # health and max health
    message.bits(5, 17)
    message.raw(100, 2)
    message.raw(100, 2)
    if weapon:
        bounded(weapon, 1, 2046)
        for value, width in [(1, 1), (0, 4), (weapon, 11), (1, 1), (clip, 9),
                             (0, 1), (0, 1), (1, 1), (1, 1), (1, 1),
                             (weapon, 11), (0, 5), (0, 12), (0, 14),
                             (1, 1), (0, 4), (weapon, 11), (ammo, 12)]:
            message.bits(value, width)
        if base_weapon and base_weapon != weapon:
            for value, width in [(1, 1), (1, 4), (base_weapon, 11), (ammo, 12)]:
                message.bits(value, width)
        message.bits(0, 1)
    else:
        message.bits(0, 3)
    message.bits(0, 15)
    previous = -1
    for number, fields in entities:
        entity_index(message, previous, number)
        entity(message, number, fields, mask, stamp)
        previous = number
    entity_index(message, previous, 2047)
    previous = -1
    for number, fields in clients:
        bounded(number, previous + 1, 31)
        message.bits(1, 1)
        message.bits(int(number == previous + 1), 1)
        if number != previous + 1:
            message.bits(number, 5)
        message.bits(0, 1)
        by_offset = dict(zip((16, 20, 24, 28, 32, 36), fields))
        selected = [(i, by_offset.get(row[0], 0)) for i, row in enumerate(CLIENT) if by_offset.get(row[0], 0)]
        message.bits(int(bool(selected)), 1)
        if selected:
            message.bits(selected[-1][0], 7)
            prior_field = -1
            for index, value in selected:
                message.bits(0, index - prior_field - 1)
                message.bits(1, 1)
                delta(message, CLIENT[index][1], value, stamp)
                prior_field = index
        previous = number
    message.bits(0, 2)
    message.raw(5)
    if len(message.data) > 1024:
        raise ValueError('3.19 snapshot exceeds 1024 bytes')
    return bytes(message.data)
