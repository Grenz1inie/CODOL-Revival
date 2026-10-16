"""3.3.3.3 server-candidate encoding; publication requires a live ready instance."""
import base64
from pathlib import Path
import re
import secrets
import struct
import threading
import time


def booking_push(sender, message):
    """Event 21 -> 0xa3e980 -> 0x6d1d80 -> Room::onBook (0x6e6f60).

    6/14 sends one untyped inner blob. Event 6 is the unrelated friend inbox.
    """
    if type(sender) is not int or not 0 < sender < 1 << 64:
        raise ValueError('invalid booking sender')
    if not isinstance(message, bytes) or not 0 < len(message) < 1024:
        raise ValueError('invalid booking message')
    inner = struct.pack('<I', len(message)) + message
    return (b'\x08\x15\0\0\0\x0a' + struct.pack('<Q', sender) + b'\x10CODOL Local\0'
            + b'\x13\x08' + struct.pack('<I', len(inner)) + inner)


def server_result(*, port, server_id, security_id, security_key):
    """Encode one loopback MatchMakingInfo (client 0x701db0 / 0xa55700).

    Unused search metadata retains the zero defaults from 0x701a30.
    This codec alone does not publish or reserve a server.
    """
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError('invalid local server port')
    if type(server_id) is not int or not 1 <= server_id < 1 << 64:
        raise ValueError('invalid server identity')
    if not isinstance(security_id, bytes) or len(security_id) != 8:
        raise ValueError('security ID must contain 8 bytes')
    if not isinstance(security_key, bytes) or len(security_key) != 16:
        raise ValueError('security key must contain 16 bytes')

    def blob(value):
        return b'\x13\x08' + struct.pack('<I', len(value)) + value

    endpoint = b'\x7f\0\0\x01' + struct.pack('<H', port)
    common_address = endpoint + bytes(24) + endpoint + b'\x01'
    result = blob(common_address) + blob(security_id)
    result += b''.join(b'\x08' + struct.pack('<I', value) for value in (0, 1, 0))
    result += b'\x10\0\x0a' + struct.pack('<Q', server_id) + b'\x10CODOL Local\0'
    result += b'\x07\0\0\0\0' * 3 + b'\x08\0\0\0\0' + b'\x07\0\0\0\0' * 3
    result += blob(security_key) + b'\x07\0\0\0\0' * 11
    return result + b'\x0a' + bytes(8) + b'\x07\0\0\0\0' * 2


def parse_query(parameters):
    if (len(parameters) != 21 or parameters[::5] != b'\x08\x08\x08\x07\0'
            or struct.unpack_from('<I', parameters, 1)[0] != 1):
        raise ValueError('unsupported server query')
    return struct.unpack_from('<I',parameters,6)[0],struct.unpack_from('<I',parameters,11)[0]


def parse_room_message(parameters):
    if (len(parameters) < 20 or parameters[0] != 10 or parameters[9:11] != b'\x13\x08'
            or parameters[-1] != 0):
        raise ValueError('invalid direct-message envelope')
    recipient, = struct.unpack_from('<Q', parameters, 1)
    size, inner_size = struct.unpack_from('<II', parameters, 11)
    if size != len(parameters)-16 or inner_size != size-4 or not 0 < inner_size < 1024:
        raise ValueError('invalid direct-message length')
    return recipient,parameters[19:-1].decode('ascii')


class StoryMatchmaking:
    """One local first-map instance; no remote commands or invented candidates."""
    server_id = 0x3333000000000001

    def __init__(self, native, profiles, directory):
        self.native, self.profiles = native, profiles
        self.directory = Path(directory)
        self.profile_path = self.directory / 'profiles'
        self.admission_path = self.directory / 'game_admissions.txt'
        self.key_path = self.directory / 'securitykey.bin'
        self.security_id, self.security_key = secrets.token_bytes(8), secrets.token_bytes(16)
        self.owner = None
        self.lock = threading.Lock()

    def start(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        self.profile_path.mkdir(exist_ok=True)
        self.admission_path.write_text('', encoding='ascii')
        self.key_path.write_bytes(self.security_key)
        self.native.start(security_id=self.security_id, profile_path=self.profile_path,
                          admission_path=self.admission_path, key_path=self.key_path)

    def _admit(self, owner):
        if type(owner) is not int or not 0 < owner < 1 << 64:
            raise ValueError('booking requires the self-profile owner')
        if self.owner not in (None, owner):
            raise ValueError('local instance already belongs to another player')
        self.profiles.export_native(owner, self.profile_path)
        temporary = self.admission_path.with_suffix('.tmp')
        temporary.write_text(f'127.0.0.1 {self.security_key.hex()} {owner:016x} '
                             f'{int(time.time())+3600} -\n', encoding='ascii')
        temporary.replace(self.admission_path)
        self.owner = owner

    def find(self, owner, parameters):
        # Observed 21/5: query ID, offset, maximum results, signed region/filter.
        offset, maximum = parse_query(parameters)
        if offset or not maximum or not self.native.ready:
            return ()
        with self.lock:
            self._admit(owner)
            if not self.native.ready:
                return ()
            return (server_result(port=self.native.port, server_id=self.server_id,
                                  security_id=self.security_id, security_key=self.security_key),)

    def message(self, owner, parameters):
        # 6/14: recipient u64, typed blob containing one untyped blob, terminator.
        recipient, text = parse_room_message(parameters)
        with self.lock:
            if owner is None or owner != self.owner or recipient != self.server_id or not self.native.ready:
                raise ValueError('no ready local reservation for this sender/recipient')
            if text.startswith('mmbook '):
                fields = text.split()
                if (len(fields) != 4 or not fields[1].isdecimal() or not fields[3].isdecimal()
                        or fields[2] != base64.b64encode(self.security_id).decode()):
                    raise ValueError('invalid booking identity')
                self._admit(owner)
                if not self.native.ready:
                    raise ValueError('native instance stopped during booking')
                return booking_push(self.server_id, b'mmbook accepted')
            if text.startswith('mmstart '):
                # The native process already initialized this map. Never execute
                # client-supplied console commands; only acknowledge this map.
                maps = [part.strip().split() for part in text[8:].split(';')
                        if re.match(r'^\s*map(?:\s|$)', part)]
                if maps not in ([['map', 'mp_cargoship']], [['map', 'coop_training_mp_cargoship']]):
                    raise ValueError('only the first map is available in this instance')
                return None
            raise ValueError('unsupported local booking command')
