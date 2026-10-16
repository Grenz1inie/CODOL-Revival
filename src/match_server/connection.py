"""Current connection messages; no native engine state or process dependencies.

SPDX-License-Identifier: AGPL-3.0-or-later
"""
import struct
import zlib
import re
import secrets

from story_wire423 import encode_gamestate, encode_packets, encode_snapshot as encode_baseline
from .input import Reader, read_move, usercmd_key, default_usercmd


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
            # 0x6d81bf computes CRC before 0x6d8a70 prepares the upload body.
            # Its first word is stale on the wire; DATA HMAC authenticates this
            # transfer. Lobby save validation has a separate CRC contract.
            if len(profile) != 32768:
                raise ValueError('invalid stats size')
            self.profile = profile
        self.length, self.fragments = compressed, fragments
        return missing


class Connection:
    """One admitted human, through stats and the map-loading handoff."""
    def __init__(self, uid, *, netconst_checksum, configstrings=(), aliases=(), recipes=(),
                 position_base=(0,0,0), map_name='mp_killhouse_sh'):
        if type(uid) is not int or not 0 < uid < 1 << 64:
            raise ValueError('invalid admitted identity')
        if map_name not in ('mp_killhouse_sh','mp_nuked'):
            raise ValueError('unsupported map identity')
        self.map_name=map_name
        self.uid = uid
        self.challenge = secrets.randbelow(0x7ffffffe)+1
        self.server_id = secrets.randbelow(254)+1
        self.checksum_feed = secrets.randbits(32)
        self.phase = 'reserved'
        self.loading_status = 0
        self.stats = StatsTransfer()
        self.received = self.sent = self.reliable = 0
        self.command = b''
        self.pending_commands = []
        self.server_commands = {0:b''}
        self.server_ack = self.published_command = 0
        self.input_bases = {0:{}}
        self.default_input = {}
        self.world_baseline_sent = False
        rows = dict(configstrings)
        # 0x57909e consumes numeric dvar 2485, not the legacy textual key.
        rows[0] = f'\\mapname\\{map_name}\\g_gametype\\dm\\2485\\2'
        rows[2] = 'cod'
        rows[3] = str(self.server_id)
        # 0x579f30 parses CS_SLOWMOTION without checking sscanf's result.
        # An absent value corrupts the native frame clock and send cadence.
        rows[6415] = '0 0 1 1'
        if len(position_base) != 3 or any(type(v) is not int or not -32767 <= v <= 32768
                                          for v in position_base):
            raise ValueError('invalid map position base')
        self.position_base = tuple(position_base)
        rows[16] = ' '.join(map(str,position_base))
        self.gamestate = encode_gamestate(map_name, 'mp', netconst_checksum,
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
        if text == 'heartbeat' and self.phase != 'reserved':
            return b'\xff'*4+b'heartbeatresponse'
        # 0x465b9a/0x465bab report stages 3 and 6 around the final map load.
        loading = re.fullmatch(r'gamestateupdate ([0-6])', text)
        if loading:
            if self.phase not in ('primed','active'):
                raise ValueError('loading update before gamestate')
            self.loading_status = int(loading[1])
            return None
        # Current client 0x465d32 includes a zero and quotes around the XUID.
        # Retain the older probe format at this text boundary.
        challenge = re.fullmatch(r'getchallenge (?:0 "([0-9a-fA-F]{16})"|([0-9a-fA-F]{16}))', text)
        if challenge:
            if int(challenge[1] or challenge[2], 16) != self.uid:
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
        return (b'\xff'*4+f'connectResponse \\mapname\\{self.map_name}\\gametype\\dm'.encode()
                +b'\\sv_maxclients\\2\\protocol\\1\\shortversion\\3.3.3.3\0')

    def queue_command(self, command):
        if not isinstance(command,bytes) or not command or b'\0' in command or len(command)>1023:
            raise ValueError('invalid reliable server command')
        sequence = max(self.server_commands)+1
        if sequence-self.server_ack > 32:
            raise ValueError('too many unacknowledged server commands')
        self.server_commands[sequence] = command
        return sequence

    def send(self, payload, *, player_fields=None):
        packets = []
        if player_fields is not None and not self.world_baseline_sent:
            # Flag 8 pins the zero delta base, but CG_DrawActiveFrame rejects
            # it for rendering. Publish it once before ordinary world frames.
            packets = self.send(encode_baseline({},server_time=0))
            self.world_baseline_sent = True
        prefix = b''.join(b'\x01'+struct.pack('<I',n)+text+b'\0'
                          for n,text in self.server_commands.items() if n > self.server_ack)
        packets.extend(encode_packets(prefix+payload, sequence=self.sent+1,
            acknowledgement=self.reliable, challenge=self.challenge, command=self.command))
        self.sent += 1
        self.published_command = max(self.server_commands)
        if player_fields is not None:
            self.default_input = default_usercmd(player_fields)
        self.input_bases[self.sent] = self.default_input
        self.input_bases = {n:b for n,b in self.input_bases.items() if n > self.sent-64}
        return packets

    def receive(self, packet, *, reply=True):
        if packet.startswith(b'\xff'*4):
            reply = self._oob(packet[4:])
            return [reply] if reply is not None else []
        if self.stats.profile is None:
            raise ValueError('valid stats required before gamestate')
        if len(packet) < 14:
            raise ValueError('truncated client netchan packet')
        sequence, server_id, ack, reliable_ack = struct.unpack_from('<IBII', packet)
        # The real client sends zero before it has received a map epoch.
        initial_epoch = (server_id == 0 and ack == 0 and reliable_ack == 0
                         and self.phase in ('connected', 'primed'))
        if not 0 < sequence < 0x20000000 or (server_id not in (255, self.server_id) and not initial_epoch):
            raise ValueError('invalid client sequence or server id')
        if ack not in self.input_bases or reliable_ack > self.published_command or reliable_ack not in self.server_commands:
            raise ValueError('client acknowledged an unsent message')
        if sequence <= self.received:
            return []
        key = (self.challenge ^ server_id ^ ack)&255
        server_command = self.server_commands[reliable_ack]
        body = bytearray(packet[13:])
        for i in range(len(body)):
            if server_command:
                key ^= (server_command[i%len(server_command)] << (i&1))&255
            body[i] ^= key
        body = bytes(body)
        reader, reliable, command = Reader(body), self.reliable, self.command
        commands = []
        while True:
            opcode = reader.bits(3)
            if opcode == 3:
                break
            if opcode == 2:
                number, candidate = reader.number(4), reader.string()
                if number > reliable:
                    if number != reliable+1:
                        raise ValueError('unsupported or missing reliable client command')
                    if candidate.startswith(b'userinfo "') and candidate.endswith(b'"'):
                        self._userinfo(candidate[10:-1].decode('ascii'))
                    elif candidate != b's' and not re.fullmatch(rb'n ([1-9]|[1-8][0-9]|9[0-8])',candidate):
                        raise ValueError('unsupported or missing reliable client command')
                    # Current action table 0xce1cc0 has IDs 1..98. These `n`
                    # notifications and score polls must not discard usercmd;
                    # simulation remains driven by that authoritative input.
                    reliable, command = number, candidate
            elif opcode in (0,1) and not commands:
                commands = read_move(reader,usercmd_key(ack,self.checksum_feed,server_command),self.input_bases[ack])
            else:
                raise ValueError('unsupported client message')
        if reader.cursor != len(body):
            raise ValueError('trailing client message bytes')
        self.received, self.reliable, self.command = sequence, reliable, command
        self.server_ack = max(self.server_ack,reliable_ack)
        self.server_commands = {n:c for n,c in self.server_commands.items() if n >= self.server_ack-32}
        self.pending_commands = commands
        if self.phase == 'connected' or not ack:
            self.phase = 'primed'
            return self.send(self.gamestate)
        return self.send(b'\x06') if reply else []
