"""Real Rust process/UDP tests using the shipped 3.3.3.3 client wire routines.

Requires the existing release binary and Nuketown package; never builds Rust or
launches the game. Stats are synthetic and stay in memory.
"""
from collections import deque
import json
from pathlib import Path
import queue
import socket
import struct
import subprocess
import sys
import threading
import time
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[5]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'games/codol/versions/v3_3_3_3/reverse/tools'), str(ROOT/'games/codol/versions/v3_3_3_3/tests')]

from client_connection423 import ClientConnection423
from client_reader423 import ClientReader423
from probe_native_connection import EncryptedPeer
from reference_match.input import FIELDS, usercmd_key
from test_match_connection import profile_bytes
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EIP, UC_X86_REG_ESP

EXE = ROOT/'runtime/builds/codol/v3_3_3_3/rust-match/release/codol-match.exe'
PACKAGE = ROOT/'runtime/builds/codol/v3_3_3_3/maps/nuketown'
UID, SID, SECURITY = 0x1234567812345678, b'12345678', bytes(range(16))


class RustProcess:
    def __init__(self):
        self.process = subprocess.Popen(
            [str(EXE), 'serve', '--package', str(PACKAGE), '--port', '0'],
            cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW)
        self.events = queue.Queue()
        self.lines = deque(maxlen=40)
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            self.lines.append(line.rstrip())
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                self.events.put(event)
        self.events.put(None)

    def diagnostics(self):
        return '\n'.join(list(self.lines))

    def event(self, name, *, request_id=None, timeout=15):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            try:
                event = self.events.get(timeout=max(.001, deadline-time.monotonic()))
            except queue.Empty:
                break
            if event is None or event.get('event') in ('error', 'match_simulation_error'):
                raise AssertionError(f'Rust process failed waiting for {name}:\n{self.diagnostics()}')
            if event.get('event') == name and (request_id is None or event.get('id') == request_id):
                return event
        raise AssertionError(f'No {name} event:\n{self.diagnostics()}')

    def send(self, **request):
        self.process.stdin.write(json.dumps(request)+'\n')
        self.process.stdin.flush()

    def close(self):
        if not self.process.stdin.closed:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.reader.join(timeout=5)
        self.process.stdout.close()


class NativeSession:
    def __init__(self, peer, reader, checksum):
        self.peer, self.reader = peer, reader
        self.sequence, self.outgoing = 0, 1
        self.reliable, self.server_command = 0, b''
        self.baselines = []
        self.challenge = int(peer.oob(
            f'getchallenge 0 "{UID:016x}"\0'.encode(), b'challengeResponse ').split()[1])
        info = f'\\xuid\\{UID:016x}\\challenge\\{self.challenge}\\name\\VGVzdA=='
        peer.oob(f'connect {UID:016x} "{info}"\0'.encode(), b'connectResponse ')
        source = zlib.compress(profile_bytes())
        for index in range((len(source)+1237)//1238):
            response = peer.oob(b'stats\0'+peer.client.stats_fragment(source, index), b'statResponse ')
        if response != b'statResponse 0':
            raise AssertionError(f'Stats incomplete: {response!r}')
        peer.send(struct.pack('<IBII', 1, 255, 0, 0)
                  +bytes([3 ^ ((self.challenge ^ 255)&255)]))
        reader.reset_netchan()
        wire = self.packet()
        self.state = self.gamestate(wire, checksum)
        offsets = struct.unpack('<7058I', reader.cpu.mem_read(0x796f2dc, 7058*4))
        size, = struct.unpack('<I', reader.cpu.mem_read(0x7996124, 4))
        pool = bytes(reader.cpu.mem_read(0x7976124, size))
        self.configstrings = {i: pool[o:pool.index(0, o)].decode('ascii')
                              for i, o in enumerate(offsets) if o}
        self.server_id = int(self.configstrings[3])

    def gamestate(self, wire, checksum):
        # Reuse test_match_snapshot's CRT-only shim: the native parser chooses
        # configstring 16 and its three destination globals for map coordinates.
        def scanf(cpu, address, size, context):
            sp = cpu.reg_read(UC_X86_REG_ESP)
            text, fmt, *dest = struct.unpack('<5I', cpu.mem_read(sp, 20))
            raw = bytes(cpu.mem_read(text, 64)).split(b'\0', 1)[0]
            format_string = bytes(cpu.mem_read(fmt, 32)).split(b'\0', 1)[0]
            values = list(map(float, raw.split()))
            if format_string != b'%f %f %f' or len(values) != 3:
                raise AssertionError(f'Unexpected map coordinate scan: {format_string!r} {raw!r}')
            for pointer, value in zip(dest, values):
                cpu.mem_write(pointer, struct.pack('<f', value))
            cpu.reg_write(UC_X86_REG_EAX, 3)
            cpu.reg_write(UC_X86_REG_EIP, 0x46e0f1)
        hook = self.reader.cpu.hook_add(UC_HOOK_CODE, scanf, begin=0x46e0ec, end=0x46e0ec)
        try:
            return self.reader.gamestate(wire, checksum=checksum)
        finally:
            self.reader.cpu.hook_del(hook)

    def packet(self):
        deadline = time.monotonic()+10
        while time.monotonic() < deadline:
            decoded = self.reader.packet(self.peer.receive(), challenge=self.challenge)
            if decoded is not None:
                self.sequence, _, payload = decoded
                return payload
        raise AssertionError('No complete native netchan message')

    def frame(self, minimum_time=0):
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            payload = self.packet()
            cursor = 0
            while payload[cursor] == 1:
                number, = struct.unpack_from('<I', payload, cursor+1)
                end = payload.index(0, cursor+5)
                if number > self.reliable:
                    self.reliable, self.server_command = number, payload[cursor+5:end]
                cursor = end+1
            if payload[cursor] != 0:
                continue
            result = self.reader.snapshot(payload[cursor:], sequence=self.sequence)
            if result['remaining'] != b'\x06':
                raise AssertionError(f'Trailing snapshot bytes: {result["remaining"]!r}')
            ready = self.reader.snapshot_frame_ready(self.sequence)
            if result['flags'] & 8:
                if ready:
                    raise AssertionError('Empty baseline passed the native draw gate')
                self.baselines.append(result)
            elif result['flags'] == 0 and ready and result['command_time'] >= minimum_time:
                self.player_data = result['player_data']
                return result
        raise AssertionError(f'No drawable native snapshot with command_time >= {minimum_time}')

    def move(self, **values):
        # Use the native default-usercmd routine on the last acknowledged,
        # natively decoded playerstate, including the map's composed weapon.
        fields = {i: struct.unpack_from('<Q' if bits == -94 else '<I', self.player_data, offset)[0]
                  for i, (offset, bits, _) in enumerate(self.reader.player_fields)}
        base = dict(zip(FIELDS, self.reader.default_usercmd(fields)))
        base.pop('direction')
        body = self.reader.usercmd(
            {**base, **values}, base=base, move=True,
            key=usercmd_key(self.sequence, self.state['checksum_feed'], self.server_command))
        key = (self.challenge ^ self.server_id ^ self.sequence)&255
        encoded = bytearray(body)
        for i in range(len(encoded)):
            if self.server_command:
                key ^= (self.server_command[i % len(self.server_command)] << (i&1))&255
            encoded[i] ^= key
        self.outgoing += 1
        self.peer.discard_queued_frames()
        self.peer.send(struct.pack('<IBII', self.outgoing, self.server_id,
                                   self.sequence, self.reliable)+encoded)


@unittest.skipUnless(sys.platform == 'win32' and EXE.is_file() and (PACKAGE/'manifest.json').is_file(),
                     'requires the local Rust release binary and Nuketown package on Windows')
class RustMatchServerTests(unittest.TestCase):
    def start(self):
        server = RustProcess()
        self.addCleanup(server.close)
        ready = server.event('ready')
        self.assertGreater(ready['port'], 0)
        self.assertEqual(ready['map'], 'mp_nuked')
        return server, ready

    def connect(self, ready, client, reader):
        peer = EncryptedPeer(ready['port'], SID, SECURITY, client, current=True)
        self.addCleanup(peer.socket.close)
        session = NativeSession(peer, reader, ready['checksum'])
        self.assertEqual((session.state['map'], session.state['game_type']), ('mp_nuked', 'dm'))
        self.assertEqual(session.state['client_number'], 0)
        self.assertEqual(session.state['remaining'], b'\x06')
        self.assertEqual(session.configstrings[6415], '0 0 1 1')
        for stage in range(1, 6):
            peer.send(b'\xff'*4+f'gamestateupdate {stage}\0'.encode())
        self.quiet(peer)
        peer.send(b'\xff'*4+b'gamestateupdate 6\0')
        first = session.frame()
        self.assertEqual(len(session.baselines), 1)
        baseline, = session.baselines
        self.assertEqual((baseline['flags'], baseline['entities'], baseline['clients'], baseline['actors']),
                         (8, 0, 0, 0))
        self.assertGreaterEqual(first['entities'], 2)
        self.assertEqual(first['clients'], 2)
        peer.send(b'\xff'*4+b'gamestateupdate 6\0')
        self.quiet(peer)
        return session, first

    def quiet(self, peer):
        peer.socket.settimeout(.2)
        try:
            with self.assertRaises(socket.timeout):
                peer.receive()
        finally:
            peer.socket.settimeout(5)

    def assert_port_released(self, port):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            probe.bind(('127.0.0.1', port))

    def test_native_udp_loading_movement_fire_reconnect_and_eof(self):
        server, ready = self.start()
        try:
            # NAT must answer before reservation; this peer must not claim it.
            intro = bytes.fromhex('0d020078563412001122334455667788997f00000131757f0000012a71')
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as nat:
                nat.settimeout(3)
                nat.sendto(intro, ('127.0.0.1', ready['port']))
                reply, address = nat.recvfrom(65535)
                self.assertEqual(address, ('127.0.0.1', ready['port']))
                self.assertEqual(reply, b'\x0c'+intro[1:])
            server.send(id=1, op='reserve', uid=UID, sid=SID.hex(), key=SECURITY.hex())
            self.assertEqual(server.event('reserved', request_id=1)['port'], ready['port'])

            # The stats writer and netchan reader use overlapping scratch memory.
            client, reader = ClientConnection423(), ClientReader423()
            session, first = self.connect(ready, client, reader)
            initial_origin = struct.unpack_from('<3f', first['player_data'], 0x1c)
            initial_clip, = struct.unpack_from('<I', first['player_data'], 0x3e0)
            self.assertGreater(initial_clip, 0)
            target_time = max(first['server_time'], first['command_time'])+100
            session.move(time=target_time, forward=127, buttons=1)
            changed = session.frame(target_time)
            origin = struct.unpack_from('<3f', changed['player_data'], 0x1c)
            clip, = struct.unpack_from('<I', changed['player_data'], 0x3e0)
            self.assertGreater(sum((a-b)**2 for a, b in zip(origin[:2], initial_origin[:2])), .01)
            self.assertEqual(clip, initial_clip-1)
            self.assertGreater(changed['server_time'], first['server_time'])

            old_address = session.peer.socket.getsockname()
            session.peer.socket.close()
            # Active snapshots provoke the real Windows ICMP/reset path.
            server.event('match_peer_reset', timeout=10)
            second, _ = self.connect(ready, client, reader)
            self.assertNotEqual(second.peer.socket.getsockname(), old_address)
            self.assertIsNone(server.process.poll())

            server.process.stdin.close()
            self.assertEqual(server.process.wait(timeout=5), 0, server.diagnostics())
            self.assert_port_released(ready['port'])
        except Exception as error:
            error.add_note('Rust process output:\n'+server.diagnostics())
            raise

    def test_stop_jsonl_exits_and_releases_udp_port(self):
        server, ready = self.start()
        server.send(id=2, op='stop')
        server.event('stopped', request_id=2)
        self.assertEqual(server.process.wait(timeout=5), 0, server.diagnostics())
        self.assert_port_released(ready['port'])


if __name__ == '__main__':
    unittest.main()
