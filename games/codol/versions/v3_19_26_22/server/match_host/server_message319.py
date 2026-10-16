"""Uncompressed 3.19 server-message primitives, traced from native readers.

diag_host319 uses these primitives for bounded sequenced replies and its
explicit game-state and first-snapshot probes. Snapshot encoding lives in
codol319_snapshot.c; the optional host probe accepts a saved payload. One
live initial snapshot advanced the client to state 10 with a black screen.
These primitives do not provide ongoing simulation, entities, or bots.
"""
import struct

SVC_SNAPSHOT = 0
SVC_SERVER_COMMAND = 1
SVC_BINARY_COMMAND = 2
SVC_GAMESTATE = 3
SVC_CONFIG_BLOCK = 4
SVC_EOF = 5


def _uint32(value):
    if not isinstance(value, int) or not 0 <= value <= 0xffffffff:
        raise ValueError('Expected an unsigned 32-bit integer')
    return value


def payload_xor(payload, *, server_sequence, challenge, reliable_command=b''):
    """Symmetric transform at 0x00470A60; bytes only, after the 8-byte header."""
    sequence = _uint32(server_sequence)
    challenge = _uint32(challenge)
    command = bytes(reliable_command).split(b'\0', 1)[0] + b'\0'
    key = (sequence ^ challenge) & 0xff
    cursor = 0
    result = bytearray(payload)
    for i in range(len(result)):
        if command[cursor] == 0:
            cursor = 0
        key ^= (command[cursor] << (i & 1)) & 0xff
        cursor += 1
        # An empty command remains at its terminating zero each iteration.
        if len(command) == 1:
            cursor = 0
        result[i] ^= key
    return bytes(result)


def server_packet(payload, *, sequence, reliable_ack=0, challenge=0, reliable_command=b''):
    """One unfragmented, uncompressed packet. No high sequence/ack flags."""
    if not isinstance(sequence, int) or not 1 <= sequence <= 0x1fffffff:
        raise ValueError('Sequence must be positive with no fragment/ack flags')
    if not isinstance(reliable_ack, int) or not 0 <= reliable_ack <= 0x7fffffff:
        raise ValueError('Reliable acknowledgement must not set compression bit')
    if not payload or len(payload) > 1024:
        raise ValueError('This initial codec supports payloads of 1..1024 bytes only')
    return struct.pack('<II', sequence, reliable_ack) + payload_xor(
        payload, server_sequence=sequence, challenge=challenge,
        reliable_command=reliable_command)


def server_command(sequence, command):
    """Service 1: reliable server command sequence followed by a C string."""
    command = command.encode('ascii')
    if b'\0' in command or len(command) > 1023:
        raise ValueError('Server command must fit the native 1024-byte buffer')
    return bytes([SVC_SERVER_COMMAND]) + struct.pack('<I', _uint32(sequence)) + command + b'\0'


def gamestate_prefix(server_command_sequence, map_name, game_type, net_config_checksum):
    """Initial fields only. A complete config block and trailer must follow.

    Reader 0x473260 reads two 32-byte C strings, then validates the checksum
    through 0x473180. Do not substitute a guessed checksum or treat this
    prefix as a complete game state.
    """
    def text32(value):
        data = value.encode('ascii')
        if b'\0' in data or len(data) > 31:
            raise ValueError('Game-state name must fit a 32-byte C string')
        return data + b'\0'
    return (bytes([SVC_GAMESTATE]) + struct.pack('<I', _uint32(server_command_sequence)) +
            text32(map_name) + text32(game_type) +
            struct.pack('<I', _uint32(net_config_checksum)))


def binary_command(sequence, data):
    """svc_binaryCommand (2): u32 reliable sequence, s16 length (<= 0x3FC), data. The client
    (00473930) stores it in the reliable command buffer as '!' 0 u16 len data; 00614AC0
    dispatches on data[0] ('%' -> 00612640, '4', '@', 'J', 'K')."""
    if not 1 <= len(data) <= 0x3FC:
        raise ValueError('Binary command must be 1..0x3FC bytes')
    return bytes([SVC_BINARY_COMMAND]) + struct.pack('<Ih', _uint32(sequence), len(data)) + bytes(data)


def register_weapon_command(weapon_index, base_weapon, camo=0, variant=0, attachments=()):
    """'%' binary command (00612640): bit 1 = weapon, 11-bit weapon index, then the structured
    record read by 00472C70 (a 11, b 8, presence bit + c 9, 4-bit count, 14-bit extras). The client
    stores '** a b c [extras]' at config 0x1748 + index and registers it (0059B560) as a composite
    weapon built from base weapon a (00431810: camo byte b, number c, attachment indices)."""
    from config_message319 import MessageWriter
    w = MessageWriter(b'%')
    w.bits(1, 1)
    w.bits(weapon_index, 11)
    w.bits(base_weapon, 11)
    w.bits(camo, 8)
    w.bits(int(variant != 0), 1)
    if variant:
        w.bits(variant, 9)
    w.bits(len(attachments), 4)
    for a in attachments:
        w.bits(a, 14)
    return bytes(w.data)
