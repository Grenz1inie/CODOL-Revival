"""Current connection messages; no native engine state or process dependencies.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import struct
import zlib
import re
import secrets

from story_wire423 import encode_gamestate, encode_packets


class StatsTransfer:
    """Assemble the current client's 1238-byte chunks before publishing stats."""
    def __init__(self):
        self.length = None
        self.fragments = {}
        self.profile = None

    def accept(self, packet):
        if len(packet) < 3:
            raise ValueError('truncated stats fragment')
        index, compressed = struct.unpack_from('<BH', packet)
        length = compressed or 32768
        count = (length+1237)//1238
        if (length > 32768 or index >= count or
                len(packet)-3 != min(1238, length-index*1238)):
            raise ValueError('invalid stats fragment range')
        if self.length is not None and self.length != compressed:
            raise ValueError('stats size changed during transfer')
        data = packet[3:]
        if index in self.fragments and self.fragments[index] != data:
            raise ValueError('stats duplicate has different content')
        fragments = {**self.fragments, index: data}
        missing = ((1 << count)-1) ^ sum(1 << i for i in fragments)
        if not missing and self.profile is None:
            profile = b''.join(fragments[i] for i in range(count))
            if compressed:
                inflater = zlib.decompressobj()
                try:
                    profile = inflater.decompress(profile, 32769)
                except zlib.error as error:
                    raise ValueError('invalid compressed stats') from error
                if not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
                    raise ValueError('incomplete or trailing compressed stats')
            if len(profile) != 32768 or struct.unpack_from('<I', profile)[0] != zlib.crc32(profile[4:]):
                raise ValueError('invalid stats size or CRC')
            self.profile = profile
        self.length, self.fragments = compressed, fragments
        return missing


class Connection:
    """One admitted human, through stats and the map-loading handoff."""
    def __init__(self, uid, *, netconst_checksum, configstrings=(), aliases=(), recipes=()):
        if type(uid) is not int or not 0 < uid < 1 << 64:
            raise ValueError('invalid admitted identity')
        self.uid = uid
        self.challenge = secrets.randbelow(0x7ffffffe)+1
        self.server_id = secrets.randbelow(254)+1
        self.checksum_feed = secrets.randbits(32)
        self.phase = 'reserved'
        self.stats = StatsTransfer()
        self.received = self.sent = self.reliable = 0
        self.command = b''
        rows = dict(configstrings)
        rows[0] = r'\mapname\mp_killhouse_sh\g_gametype\dm\sv_maxclients\2'
        rows[3] = str(self.server_id)
        self.gamestate = encode_gamestate('mp_killhouse_sh', 'dm', netconst_checksum,
            command_sequence=0, client_number=0, checksum_feed=self.checksum_feed,
            ordinary=sorted(rows.items()), aliases=aliases, recipes=recipes)

    def _userinfo(self, value):
        if (not value.startswith('\\') or len(value) >= 1024 or
                any(ord(c) < 32 or ord(c) >= 127 or c in '";' for c in value)):
            raise ValueError('invalid userinfo')
        pairs = value[1:].split('\\')
        if len(pairs) % 2 or any(not key for key in pairs[::2]):
            raise ValueError('invalid userinfo pairs')
        fields = dict(zip(pairs[::2], pairs[1::2]))
        if len(fields) != len(pairs)//2:
            raise ValueError('duplicate userinfo key')
        if fields.get('xuid', '').lower() != f'{self.uid:016x}':
            raise ValueError('userinfo identity does not match reservation')
        return fields

    def _oob(self, packet):
        if packet.startswith(b'stats\0'):
            if self.phase == 'reserved':
                raise ValueError('stats require a connected client')
            return b'\xff'*4+f'statResponse {self.stats.accept(packet[6:])}\0'.encode()
        try:
            text = packet.removesuffix(b'\0').decode('ascii')
        except UnicodeDecodeError as error:
            raise ValueError('invalid connection text') from error
        challenge = re.fullmatch(r'getchallenge ([0-9a-fA-F]{16})', text)
        if challenge:
            if int(challenge[1], 16) != self.uid:
                raise ValueError('challenge identity does not match reservation')
            return b'\xff'*4+f'challengeResponse {self.challenge}\0'.encode()
        connect = re.fullmatch(r'connect ([0-9a-fA-F]{16}) "([^"\x00]*)"', text)
        if not connect or int(connect[1], 16) != self.uid:
            raise ValueError('invalid connect identity or command')
        fields = self._userinfo(connect[2])
        if fields.get('challenge') != str(self.challenge):
            raise ValueError('connect challenge mismatch')
        if self.phase == 'reserved':
            self.phase = 'connected'
        # The current OOB dispatcher accepts the connection here; map loading
        # context is separately conveyed and verified by SVC_GAMESTATE.
        return (b'\xff'*4+b'connectResponse \\mapname\\mp_killhouse_sh\\gametype\\dm'
                b'\\sv_maxclients\\2\\protocol\\1\\shortversion\\3.3.3.3\0')

    def send(self, payload):
        packets = encode_packets(payload, sequence=self.sent+1,
            acknowledgement=self.reliable, challenge=self.challenge, command=self.command)
        self.sent += 1
        return packets

    def receive(self, packet):
        if packet.startswith(b'\xff'*4):
            return [self._oob(packet[4:])]
        if self.stats.profile is None:
            raise ValueError('valid stats required before gamestate')
        if len(packet) < 14:
            raise ValueError('truncated client netchan packet')
        sequence, server_id, ack, reliable_ack = struct.unpack_from('<IBII', packet)
        if not 0 < sequence < 0x20000000 or server_id not in (255, self.server_id):
            raise ValueError('invalid client sequence or server id')
        if ack > self.sent or reliable_ack:
            raise ValueError('client acknowledged an unsent message')
        if sequence <= self.received:
            return []
        key = (self.challenge ^ server_id ^ ack)&255
        body = bytes(value ^ key for value in packet[13:])
        cursor, reliable, command = 0, self.reliable, self.command
        while cursor < len(body) and body[cursor] == 26:
            if cursor+5 > len(body) or b'\0' not in body[cursor+5:]:
                raise ValueError('truncated reliable client command')
            number, = struct.unpack_from('<I', body, cursor+1)
            end = body.index(0, cursor+5)
            candidate = body[cursor+5:end]
            if number > reliable:
                if number != reliable+1 or not candidate.startswith(b'userinfo "') or not candidate.endswith(b'"'):
                    raise ValueError('unsupported or missing reliable client command')
                self._userinfo(candidate[10:-1].decode('ascii'))
                reliable, command = number, candidate
            cursor = end+1
        if body[cursor:] not in (b'', b'\x03'):
            raise ValueError('unsupported client message')
        self.received, self.reliable, self.command = sequence, reliable, command
        if self.phase == 'connected' or not ack:
            self.phase = 'primed'
            return self.send(self.gamestate)
        return self.send(b'\x06')
