"""Owned loopback connection probe; current client readers, no game/saves edited."""
import base64
import hmac
import json
from pathlib import Path
import secrets
import socket
import struct
import sys
import time
import traceback
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from client_connection423 import ClientConnection423
from client_reader423 import ClientReader423
from dw_matchmaking import StoryMatchmaking
from dw_progression import PrivateProfileStore
from native_server import NativeServer


class EncryptedPeer:
    """Reference DATA framing with Tiger executed from the current client."""
    def __init__(self, port, sid, security, client):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # x86 emulation consumes a burst slower than the real game; keep a full
        # initial snapshot queued instead of dropping its final fragments.
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4*1024*1024)
        self.socket.bind(('127.0.0.1', 0))
        self.socket.settimeout(5)
        self.endpoint = ('127.0.0.1', port)
        self.client, self.sent, self.received = client, 0, 0
        self.deferred = []
        self.tag = secrets.randbelow(65535)+1
        self.socket.sendto(struct.pack('<BBHHH', 1, 2, 0, 0, self.tag)+sid, self.endpoint)
        ack, _ = self.socket.recvfrom(65535)
        assert len(ack) == 38 and ack[:4] == struct.pack('<BBH', 2, 2, self.tag) and ack[30:] == sid
        self.server_tag, = struct.unpack_from('<H', ack, 16)
        private = ec.generate_private_key(ec.SECP224R1())
        numbers = private.public_key().public_numbers()
        def integer(value):
            data = value.to_bytes(28, 'big')
            data = (b'\0' if data[0]&128 else b'')+data
            return b'\x02'+bytes([len(data)])+data
        content = b'\x03\x02\x07\0\x02\x01\x1c'+integer(numbers.x)+integer(numbers.y)
        public = (b'\x30'+bytes([len(content)])+content).ljust(100, b'\0')
        echo = struct.pack('<BBHH', 3, 2, self.server_tag, 0)+ack+bytes(37)+sid+public
        self.socket.sendto(echo, self.endpoint)
        cookie, _ = self.socket.recvfrom(65535)
        assert len(cookie) == 114 and cookie[:6] == struct.pack('<BBHH', 4, 2, self.tag, 0) and cookie[106:] == sid
        key = cookie[6:106]
        cursor, coordinates = 9, []
        for _ in range(2):
            assert key[cursor] == 2
            length = key[cursor+1]
            coordinates.append(int.from_bytes(key[cursor+2:cursor+2+length], 'big'))
            cursor += 2+length
        peer = ec.EllipticCurvePublicNumbers(*coordinates, ec.SECP224R1()).public_key()
        self.key = client.tiger(private.exchange(ec.ECDH(), peer)+security)

    def crypt(self, data, counter):
        iv = int.from_bytes(self.client.tiger(struct.pack('<I', counter))[:16], 'little')
        encryptor = Cipher(algorithms.AES(self.key), modes.ECB()).encryptor()
        stream = encryptor.update(b''.join(((iv+i) % (1<<128)).to_bytes(16, 'little')
                                           for i in range((len(data)+15)//16)))+encryptor.finalize()
        return bytes(a^b for a,b in zip(data, stream))

    def send(self, plain):
        self.sent += 1
        header = struct.pack('<BBHH', 6, 2, self.server_tag, self.sent & 65535)
        data = self.crypt(plain, self.sent)
        self.socket.sendto(header+hmac.digest(self.key, header+data, 'sha1')[:8]
                           +struct.pack('<H', len(data))+data, self.endpoint)

    def receive(self, *, allow_deferred=True):
        if allow_deferred and self.deferred:
            return self.deferred.pop(0)
        packet, address = self.socket.recvfrom(65535)
        assert address == self.endpoint and packet[:4] == struct.pack('<BBH', 6, 2, self.tag)
        counter, = struct.unpack_from('<H', packet, 4)
        counter += self.received & ~65535
        if counter+32768 < self.received:
            counter += 65536
        elif counter-32768 > self.received:
            counter -= 65536
        assert counter > self.received
        assert struct.unpack_from('<H', packet, 14)[0] == len(packet)-16
        assert hmac.compare_digest(packet[6:14], hmac.digest(self.key, packet[:6]+packet[16:], 'sha1')[:8])
        self.received = counter
        return self.crypt(packet[16:], counter)

    def oob(self, request, prefix):
        self.send(b'\xff'*4+request)
        deadline = time.monotonic()+5
        while time.monotonic() < deadline:
            response = self.receive(allow_deferred=False)
            if response.startswith(b'\xff'*4):
                assert response.startswith(b'\xff'*4+prefix), response[:250]
                return response[4:].rstrip(b'\0')
            self.deferred.append(response)
        raise TimeoutError(f'no {prefix!r} reply')

    def discard_queued_frames(self):
        # The probe requests full snapshots. Discard frames queued while x86
        # parsing ran, so the next observation can include the next input.
        self.socket.setblocking(False)
        try:
            while True:
                self.socket.recvfrom(65535)
        except BlockingIOError:
            pass
        finally:
            self.socket.settimeout(5)


def probe():
    native = NativeServer(ROOT, port=28971)
    profiles = PrivateProfileStore(ROOT/'runtime/data/private-profiles', ROOT/'runtime/backups/private-profiles')
    uid = 0xe94a180c65d3c23b
    directory = ROOT/'research/experiments/story-native'/('connection-'+secrets.token_hex(4))
    service = StoryMatchmaking(native, profiles, directory)
    result = {'gameplay_verified': False, 'steps': []}
    peer = None
    try:
        service.start()
        result['home'] = str(native.home)
        result['steps'].append('native publication ready')
        service.find(uid, bytes.fromhex('08010000000800000000080a000000079b1ff0d600'))
        client, reader = ClientConnection423(), ClientReader423()
        peer = EncryptedPeer(native.port, service.security_id, service.security_key, client)
        result['steps'].append('encrypted handshake')
        challenge = int(peer.oob(f'getchallenge {uid:016x}\0'.encode(), b'challengeResponse ').split()[1])
        name = base64.b64encode(b'LocalProbe').decode()
        info = (f'\\name\\{name}\\xuid\\{uid:016x}\\2490\\-1157214325\\challenge\\{challenge}'
                f'\\qport\\{peer.socket.getsockname()[1]}\\rate\\25000\\snaps\\20')
        result['connect_response'] = peer.oob(f'connect {uid:016x} "{info}"\0'.encode(), b'connectResponse ').decode()
        result['steps'].append('challenge/connect accepted')
        # A declared minimal fixture, not the lobby's stripped public-profile
        # blob. The full game supplies its own stats; formal saves stay untouched.
        schema = json.loads((ROOT/'research/evidence/live-player-schema.json').read_text())['schemas']['mp/playerdata.def']
        public = bytearray(32768)
        struct.pack_into('<II', public, 4, schema['header'][0], schema['header'][1])
        for i, value in enumerate((545, 104, 0, 0, 0, 0, 0, 0, 0)):
            struct.pack_into('<I', public, 4+schema['offsets'][577+i], value)
        struct.pack_into('<I', public, 0, zlib.crc32(public[4:]))
        packed = zlib.compress(public)
        result['public_stats_source'] = 'minimal current-schema fixture: cha_INFbaseA + han_hands'
        for index in range((len(packed)+1237)//1238):
            response = peer.oob(b'stats\0'+client.stats_fragment(packed, index), b'statResponse ')
        assert response == b'statResponse 0', response
        result['steps'].append('current-client stats upload complete')
        peer.send(struct.pack('<IBII', 1, 255, 0, 0)
                  +bytes([3 ^ ((challenge ^ 255)&255)]))
        reader.reset_netchan()
        while True:
            packet = peer.receive()
            decoded = reader.packet(packet, challenge=challenge & 0xffffffff)
            if decoded is None:
                continue
            sequence, acknowledgement, payload = decoded
            if payload == b'\x06':
                continue  # A connection keepalive may precede the stats ACK.
            (directory/'gamestate.bin').write_bytes(payload)
            if payload[0] != 3:
                raise ValueError(f'unexpected initial message {payload[:80]!r}')
            log = next(native.home.rglob('qconsole.log')).read_text(errors='replace')
            import re
            crc = int(re.search(r'netconst checksum=([0-9a-f]+)', log)[1], 16)
            result['gamestate'] = reader.gamestate(payload, checksum=crc)
            result['gamestate']['remaining'] = result['gamestate']['remaining'].hex()
            cursor = payload.index(0, 5)+1
            cursor = payload.index(0, cursor)+5
            rows, _ = reader.configstrings(payload[cursor+1:])
            result['configstrings'] = rows
            result['steps'].append('gamestate consumed by current client')
            break
        server_id = int(rows[3]) & 255
        reliable_sequence = result['gamestate']['command_sequence']
        server_command = b''
        requested_weapon = None
        outgoing_sequence = 1
        def send_body(body):
            nonlocal outgoing_sequence
            outgoing_sequence += 1
            key = (challenge ^ server_id ^ sequence)&255
            encoded = bytearray(body)
            for i in range(len(encoded)):
                if server_command:
                    key ^= (server_command[i % len(server_command)] << (i&1)) & 255
                encoded[i] ^= key
            peer.send(struct.pack('<IBII', outgoing_sequence, server_id, sequence, reliable_sequence)+encoded)
        command = f'userinfo "{info}"'.encode()
        send_body(b'\x1a'+struct.pack('<I', 1)+command+b'\0')
        while True:
            decoded = reader.packet(peer.receive(), challenge=challenge & 0xffffffff, command=command)
            if decoded is not None and decoded[1] == 1:
                result['steps'].append('reliable userinfo acknowledged')
                break
        # Keep the initial gamestate ACK, so the first command has a zero base.
        userkey = sequence ^ result['gamestate']['checksum_feed']
        body = reader.usercmd({'time':100, 'forward':127}, key=userkey, move=True)
        send_body(body)
        def receive_frame(minimum_time=0):
            nonlocal sequence, reliable_sequence, server_command, requested_weapon
            end = time.monotonic()+5
            while time.monotonic() < end:
                packet = peer.receive()
                with (directory/'frame-packets.bin').open('ab') as capture:
                    capture.write(struct.pack('<I', len(packet))+packet)
                decoded = reader.packet(packet, challenge=challenge & 0xffffffff, command=command)
                if decoded is None:
                    result['last_unassembled_packet'] = packet[:16].hex()
                    result['netchan_prefix'] = bytes(reader.cpu.mem_read(0x30180158, 64)).hex()
                    continue
                sequence, _, payload = decoded
                (directory/'first-frame.bin').write_bytes(payload)
                result['first_frame_prefix'] = payload[:80].hex()
                cursor = 0
                while cursor < len(payload) and payload[cursor] == 1:
                    number, = struct.unpack_from('<I', payload, cursor+1)
                    tail = payload.index(0, cursor+5)
                    text = payload[cursor+5:tail]
                    if number > reliable_sequence:
                        reliable_sequence, server_command = number, text
                        result.setdefault('server_commands', []).append(text.decode())
                        if text.startswith(b'a '):
                            # 0x57d560 case 0x61 -> 0x562260 selects the weapon
                            # requested by switchToWeapon; the next usercmd carries it.
                            requested_weapon = int(text[2:])
                        if text.startswith(b't '):
                            raise ValueError(f'server disconnect: {text.decode()}')
                    cursor = tail+1
                if payload[cursor] == 0:
                    if struct.unpack_from('<I', payload, cursor+1)[0] < minimum_time:
                        continue
                    frame = reader.snapshot(payload[cursor:], sequence=sequence)
                    state = bytes(reader.cpu.mem_read(0x7996128, 0x3524))
                    frame['origin'] = struct.unpack_from('<3f', state, 0x1c)
                    frame['weapon'], = struct.unpack_from('<I', state, 0x340)
                    frame['clips'] = [struct.unpack_from('<3I', state, 0x3dc+i*12) for i in range(15)]
                    if frame['command_time'] >= minimum_time:
                        return frame, state
                    continue
                if payload[cursor:] != b'\x06':
                    raise ValueError(f'unexpected server message {payload[cursor:cursor+80]!r}')
                send_body(b'\x03')  # Drain deferred configstrings before the frame.
            raise ValueError('no acknowledged snapshot after user command')

        frame, state = receive_frame()
        result['snapshot'] = frame
        result['steps'].append('spawn snapshot consumed by current client')
        for action, forward, buttons in [('move', 127, 0), ('fire', 0, 1)]:
            initial = frame
            for _ in range(6):
                fields = {i: struct.unpack_from('<Q' if bits == -94 else '<I', state, offset)[0]
                          for i, (offset, bits, _) in enumerate(reader.player_fields)}
                defaults = reader.default_usercmd(fields)
                base = dict(zip(('time','buttons','pitch','yaw','roll'), defaults[:5]))
                base.update(weapon=defaults[6], offhand=defaults[7], alt=defaults[8],
                            melee_target=defaults[11])
                target_time = frame['server_time']+50
                values = base | {'time': target_time, 'forward': forward, 'buttons': buttons}
                if requested_weapon is not None:
                    values['weapon'] = requested_weapon
                hashed = sum(c*(119+i) for i, c in enumerate(server_command[:32])) & 0xffffffff
                userkey = sequence ^ result['gamestate']['checksum_feed'] ^ hashed ^ (hashed>>10) ^ (hashed>>20)
                peer.discard_queued_frames()
                send_body(reader.usercmd(values, key=userkey, base=base, move=True))
                frame, state = receive_frame(target_time)
            result[action] = {'before': initial, 'after': frame}
            if action == 'move':
                assert sum((frame['origin'][i]-initial['origin'][i])**2 for i in range(2)) > 1, 'no horizontal movement'
            else:
                assert any(a[0] == b[0] != 0 and a[1] < b[1]
                           for a, b in zip(frame['clips'], initial['clips'])), 'no ammunition consumed'
            result['steps'].append(f'{action} changed authoritative state consumed by current client')
        result['protocol_verified'] = True
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
        result['traceback'] = traceback.format_exc()
    finally:
        if peer:
            peer.socket.close()
        native.close()
        result['home'] = str(native.home)
        result['native_exit'] = native.process.returncode if native.process else None
        serialized = json.dumps(result, indent=2, default=lambda value: value.hex())
        (ROOT/'research/evidence/native-connection-latest.json').write_text(serialized, encoding='utf-8')
    print(serialized, flush=True)
    return 1 if 'error' in result else 0


if __name__ == '__main__':
    sys.exit(probe())
