"""Inverse of the shipped 0x5a1be0 usercmd writer.

Adapted from codol_usercmd.c; SPDX-License-Identifier: AGPL-3.0-or-later.
"""
import struct

FIELDS = ('time','buttons','pitch','yaw','roll','direction','weapon','offhand','alt',
          'melee_yaw','melee_dist','melee_target','location_x','location_y',
          'location_angle','remote_x','remote_y')


class Reader:
    """Bit pools occupy bytes in the same cursor as ordinary byte fields."""
    def __init__(self, data):
        self.data, self.cursor, self.bit = data, 0, 0

    def raw(self, size):
        if self.cursor+size > len(self.data):
            raise ValueError('truncated client message')
        value = self.data[self.cursor:self.cursor+size]
        self.cursor += size
        return value

    def number(self, size):
        return int.from_bytes(self.raw(size), 'little')

    def bits(self, width):
        value = 0
        for i in range(width):
            if self.bit % 8 == 0:
                self.bit = self.cursor*8
                self.raw(1)
            value |= ((self.data[self.bit//8] >> (self.bit%8))&1) << i
            self.bit += 1
        return value

    def string(self):
        end = self.data.find(b'\0', self.cursor)
        if end < 0 or end-self.cursor > 1023:
            raise ValueError('invalid client command string')
        return self.raw(end-self.cursor+1)[:-1]


def read_usercmd(reader, key, base):
    state = {name:base.get(name,0) for name in FIELDS}
    state['time'] = ((state['time']+reader.number(1))&0xffffffff
                     if reader.bits(1) else reader.number(4))
    expected = 7

    def delta(name, mask, width, raw=False):
        if reader.bits(1):
            value = reader.number(width//8) if raw else reader.bits(width)
            state[name] = value ^ (mask & ((1 << width)-1))

    if reader.bits(1) ^ (key&1):
        if not (reader.bits(1) ^ (key&1)):
            expected = 2
            k = key ^ state['time']
            state['buttons'] = (state['buttons'] & ~1) | (reader.bits(1) ^ (k&1))
            delta('pitch',k,16,True)
            delta('yaw',k,16,True)
            delta('direction',k,4)
        else:
            expected = 5
            fire = reader.bits(1) ^ (key&1)
            delta('pitch',key,16,True)
            delta('yaw',key,16,True)
            delta('direction',key,4)
            k = key ^ state['time']
            delta('roll',k,16,True)
            upper = (reader.bits(29) ^ (k & ((1 << 29)-1))
                     if reader.bits(1) else state['buttons'] >> 1)
            state['buttons'] = upper*2 | fire
            for name in ('weapon','offhand','alt'):
                delta(name,k,10)
            if state['buttons'] & 0x20000:
                for name in ('location_x','location_y','location_angle'):
                    delta(name,k,8,True)
            if state['buttons'] & 0x200000:
                for name in ('remote_x','remote_y'):
                    delta(name,k,8,True)
            if state['buttons'] & 4:
                delta('melee_yaw',k,16,True)
                delta('melee_dist',k,8)
                delta('melee_target',k,11)
    if reader.bits(3) != expected:
        raise ValueError('invalid usercmd trailing tag')
    return state


def decode_usercmd(wire, *, key, base=None):
    reader = Reader(wire)
    result = read_usercmd(reader,key,base or {})
    if reader.cursor != len(wire):
        raise ValueError('trailing usercmd bytes')
    return result


def read_move(reader, key, base):
    count = reader.number(1)
    if not 1 <= count <= 32:
        raise ValueError('invalid usercmd count')
    commands = []
    for _ in range(count):
        base = read_usercmd(reader,key,base)
        commands.append(base)
    # Client-reported predicted origin/time is not authoritative simulation.
    reader.raw(20)
    return commands


def decode_move(wire, *, key, base=None):
    reader = Reader(wire)
    if reader.bits(3) not in (0,1):
        raise ValueError('expected client move message')
    commands = read_move(reader,key,base or {})
    if reader.bits(3) != 3 or reader.cursor != len(wire):
        raise ValueError('invalid move message terminator')
    return commands


def usercmd_key(acknowledgement, checksum, command=b''):
    value = sum((46 if c >= 128 or c == 37 else c)*(119+i)
                for i,c in enumerate(command.split(b'\0',1)[0][:32])) & 0xffffffff
    return acknowledgement ^ checksum ^ value ^ (value >> 10) ^ (value >> 20)


def default_usercmd(player):
    """Current 0x5a18e0 delta base, derived from the acknowledged playerstate."""
    command = dict.fromkeys(FIELDS,0)
    real = lambda index: struct.unpack('<f',struct.pack('<I',player.get(index,0)))[0]
    f32 = lambda value: struct.unpack('<f',struct.pack('<f',value))[0]
    command.update(weapon=player.get(39,0),alt=player.get(40,0),offhand=player.get(53,0))
    command['pitch'] = round(f32(f32(real(19)-real(70))*f32(65536/360)))&65535
    command['yaw'] = round(f32(f32(real(18)-real(45))*f32(65536/360)))&65535
    if player.get(54,0)&0x1000:
        flags = player.get(28,0)
        command['buttons'] = 0x100 if flags&8 else 0x200 if flags&4 else 0
        if real(41):
            command['buttons'] |= 0x800
        command['melee_target'] = 2047
    return command
