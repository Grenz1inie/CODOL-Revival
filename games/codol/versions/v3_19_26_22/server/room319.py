"""3.19 local-host channel admission; native room logic owns the visible roster."""
from base64 import b64encode
import json
from pathlib import Path
import struct
import subprocess


def native_manifest(owner, name, roster=None):
    executable = (Path(__file__).resolve().parents[5]
                  / 'runtime/builds/codol/v3_19_26_22/rust-match/release/codol-match319.exe')
    request = {'uid': owner, 'name': name}
    if roster is not None:
        request['roster'] = list(roster)
    result = subprocess.run([str(executable), 'room'], input=json.dumps(request),
        capture_output=True, text=True, encoding='utf-8', timeout=10,
        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise ValueError('Rust room admission failed: ' + result.stderr.strip())
    return json.loads(result.stdout)


def u32(value): return b'\x08' + struct.pack('<I', value)
def u64(value): return b'\x0a' + struct.pack('<Q', value)
def text(value): return b'\x10' + b64encode(value.encode('utf-8')) + b'\0'
def blob(value): return b'\x13' + u32(len(value)) + value


def channel_info(channel, owner, count):
    # Native bdChannelInfo reader 0xb96f70.
    return u64(channel) + u32(count) + u32(18) + u64(owner) + b'\x01\0\x01\0' + u32(0)


def member_event(event, channel, owner, player, count):
    # Native event 9/10, version 2 -> 0xb7b4b0.
    return (u32(event) + u64(player['uid']) + text(player['name']) + u64(channel)
            + b'\x03\x02' + u32(0) + channel_info(channel, owner, count))


def message_event(channel, player, message):
    # Event 7 -> 0xb7b300; 0x6371f0 consumes an untyped length-prefixed blob.
    return (u32(7) + u64(player['uid']) + text(player['name']) + u64(channel)
            + blob(struct.pack('<I', len(message)) + message) + u32(1))


def messages(payload, uid):
    """Flatten native aggregate message 1, retaining only broadcasts/our bot target."""
    pending = [payload]
    result = []
    while pending:
        data = pending.pop()
        value, position = int.from_bytes(data, 'little'), 0
        def read(width):
            nonlocal position
            if position + width > len(data) * 8:
                raise ValueError('truncated room message')
            field = (value >> position) & ((1 << width) - 1)
            position += width
            return field
        if read(1) != 0:
            raise ValueError('typed room bit buffer unsupported')
        if read(8) != 1:
            result.append(data)
            continue
        count = read(32)
        if count > 100:
            raise ValueError('room aggregate too large')
        for _ in range(count):
            target = read(64) if read(1) else 0
            size = read(32)
            if size > 2048:
                raise ValueError('room message too large')
            message = read(size * 8).to_bytes(size, 'little')
            if target in (0, uid):
                pending.append(message)
    return result


class Room:
    def __init__(self, owner, manifest):
        self.owner = owner
        self.manifest = manifest
        self.channel = 0
        self.next_channel = 0x31900001
        self.phase = 'idle'
        self.players = []
        self.observed_count = 0
        self.roster = None
        self.ready = False

    def match_request(self):
        if self.phase == 'bots_sent' and self.ready and self.observed_count == 18 and self.roster:
            return {'uid': self.owner, 'name': self.players[0]['name'], 'roster': list(self.roster)}
        return None

    def handle(self, body, transaction):
        if len(body) < 3:
            return None, []
        service, _, task = body[:3]
        if (service, task) == (21, 5):
            if body[3:8] != u32(3):
                return None, []  # Query 1 refreshes sessions inside the existing room.
            # Query 3 field positions verified in the current client's real capture.
            selected = (len(body) >= 63 and body[3:8] == u32(3)
                        and body[43:48] == b'\x07' + struct.pack('<I', 797)
                        and body[48:53] == b'\x07' + struct.pack('<I', 110))
            self.phase = 'selected' if selected else 'idle'
            self.channel, self.players, self.observed_count = 0, [], 0
            self.roster, self.ready = None, False
            return None, []
        if self.phase == 'idle' or service != 11:
            return None, []
        if task == 13:
            self.players = self.manifest()['players']
            self.channel = self.next_channel
            self.next_channel += 1
            self.phase = 'created'
            reply = u64(transaction) + u32(0) + b'\x03\x0d' + u32(1) + u32(1)
            return reply + channel_info(self.channel, self.owner, 1), []
        if task != 4 or not self.channel or len(body) < 23:
            return None, []
        if body[3:12] != u64(self.channel) or body[12:14] != b'\x13\x08':
            return None, []
        size = struct.unpack_from('<I', body, 14)[0]
        wrapped = body[18:18 + size]
        if len(wrapped) != size or size < 4 or body[18 + size:] != u32(1) + b'\0':
            return None, []
        length = struct.unpack_from('<I', wrapped)[0]
        if length > size - 4:
            return None, []
        first_bot = self.players[1]
        if self.phase == 'created':
            self.phase = 'host_requested'
            pushes = [member_event(9, self.channel, self.owner, player, i + 2)
                      for i, player in enumerate(self.players[1:])]
            return None, pushes + [message_event(self.channel, first_bot, b'\x1a\0')]
        try:
            if self.phase == 'bots_sent':
                ready = [payload for payload in messages(wrapped[4:4 + length], self.owner)
                         if payload in (b'\x20\0', b'\x20\x02')]
                if ready:
                    self.ready = ready[-1] == b'\x20\x02'
                    # Native 0x6301a0 sends message 16; only its channel echo
                    # reaches 0x634870 and updates the sender's ready bit.
                    return None, [message_event(self.channel, self.players[0], payload) for payload in ready]
            incoming = messages(wrapped[4:4 + length], first_bot['uid'])
        except ValueError:
            return None, []
        for payload in incoming:
            if len(payload) < 6 or (payload[0] >> 1 | (payload[1] & 1) << 7) != 14:
                continue
            if self.phase == 'host_requested':
                # Rust recovers the host's actual team and compatibility fields.
                self.players = self.manifest(payload)['players']
                self.roster = payload
                self.phase = 'bots_sent'
                pushes = [message_event(self.channel, player, bytes(player['join']))
                          for player in self.players[1:]]
                return None, pushes + [message_event(self.channel, self.players[1], b'\x1a\0')]
            self.observed_count = (int.from_bytes(payload[:6], 'little') >> 9) & 0xffffffff
        return None, []
