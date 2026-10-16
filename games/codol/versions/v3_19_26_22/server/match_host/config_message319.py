"""3.19 config-block encoding for native reader 0x472D80.

Byte fields advance the byte cursor but preserve partially consumed bit bytes.
This is not a conventional contiguous bit stream. Constants need a verified
type table; indices backed by native constants cannot be sent as literals.
"""
import struct
from dataclasses import dataclass


class MessageWriter:
    def __init__(self, initial=b''):
        self.data = bytearray(initial)
        self.bit = 0

    def raw(self, data):
        self.data.extend(data)

    def bits(self, value, width):
        if not isinstance(value, int) or not 1 <= width <= 31 or not 0 <= value < 1 << width:
            raise ValueError('Bit field outside its unsigned range')
        for shift in range(width):
            if self.bit & 7 == 0:
                self.bit = len(self.data) * 8
                self.data.append(0)
            self.data[self.bit >> 3] |= ((value >> shift) & 1) << (self.bit & 7)
            self.bit += 1

    def text(self, value):
        data = value.encode('ascii')
        if b'\0' in data or b'%' in data or len(data) > 8191:
            raise ValueError('Config literal must be ASCII, NUL-free, percent-free, <=8191 bytes')
        self.raw(data + b'\0')


@dataclass(frozen=True)
class StructuredConfig:
    """Native text '** a b c [extra...]' decoded by 0x472C70."""
    a: int
    b: int
    c: int = 0
    extra: tuple = ()

    def text(self):
        return '** %d %d %d%s' % (self.a, self.b, self.c,
                                  ''.join(' %d' % n for n in self.extra))


def write_config_block(writer, literals, numeric, structured, *, type_table):
    """Write counts/records only; caller writes service byte 4 first.

    numeric values decode to '* N', not bare decimal numbers. All categories
    have independent previous-index counters starting at -1.
    """
    if len(type_table) != 0x31d9:
        raise ValueError('A complete verified 3.19 index type table is required')
    groups = [dict(literals), dict(numeric), dict(structured)]
    indices = []
    for group in groups:
        for index in group:
            if not isinstance(index, int) or not 0 <= index < 0x31d9:
                raise ValueError('Config index out of range')
            indices.append(index)
    if len(indices) != len(set(indices)):
        raise ValueError('Duplicate index across config categories')
    if len(groups[0]) > 0x31d9 or len(groups[1]) > 1023 or len(groups[2]) > 2047:
        raise ValueError('Too many entries for native count fields')
    # Validate into a temporary writer so failures cannot leave partial output.
    staged = MessageWriter(writer.data)
    staged.bit = writer.bit
    def index_code(index, previous):
        staged.bits(int(index == previous + 1), 1)
        if index != previous + 1:
            staged.bits(index, 14)
    staged.raw(struct.pack('<H', len(groups[0])))
    previous = -1
    for index, text in sorted(groups[0].items()):
        if type_table[index] < 0x17 and type_table[index] != 0x15:
            raise ValueError('Literal index is owned by a native constant table')
        index_code(index, previous)
        staged.text(text)
        previous = index
    staged.bits(len(groups[1]), 10)
    previous = -1
    for index, number in sorted(groups[1].items()):
        index_code(index, previous)
        staged.bits(number, 11)
        previous = index
    staged.bits(len(groups[2]), 11)
    previous = -1
    for index, value in sorted(groups[2].items()):
        if not isinstance(value, StructuredConfig):
            raise ValueError('Expected StructuredConfig')
        index_code(index, previous)
        staged.bits(value.a, 11)
        staged.bits(value.b, 8)
        staged.bits(int(value.c != 0), 1)
        if value.c:
            staged.bits(value.c, 9)
        staged.bits(len(value.extra), 4)
        for extra in value.extra:
            staged.bits(extra, 14)
        previous = index
    decoded_size = 1 + sum(len(s.encode('ascii')) + 1 for s in groups[0].values())
    decoded_size += sum(len('* %d' % n) + 1 for n in groups[1].values())
    decoded_size += sum(len(v.text()) + 1 for v in groups[2].values())
    if decoded_size > 0x20000:
        raise ValueError('Config strings exceed native pool capacity')
    writer.data, writer.bit = staged.data, staged.bit


def gamestate_message(*, map_name, game_type, net_config_checksum, type_table,
                      literals, numeric=None, structured=None,
                      server_command_sequence=0, client_number=0, checksum_feed=0):
    """Complete wire layout; map defaults/content still require runtime validation."""
    from server_message319 import gamestate_prefix, _uint32
    if not isinstance(client_number, int) or not 0 <= client_number <= 18:
        raise ValueError('Client number must be in native range 0..18')
    writer = MessageWriter(gamestate_prefix(server_command_sequence, map_name,
                                           game_type, net_config_checksum))
    writer.raw(b'\x04')
    write_config_block(writer, literals, numeric or {}, structured or {}, type_table=type_table)
    writer.raw(b'\x05' + struct.pack('<II', client_number, _uint32(checksum_feed)) + b'\x05')
    return bytes(writer.data)
