"""In-memory wire tests: no listeners, game launches, or capture-file writes."""
import hashlib
import hmac
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dw_lobby import SESSION_KEY, handle_lobby, stun_reply


# Real CODOL capture 20261014T034553490974-lobby-request.bin, all 28 bytes.
HELLO = bytes.fromhex('c8000000c8000000d2000000d2000000000008006b8b867dafe4229e')
ACK = bytes.fromhex('16000000ab81d2000000' + '1337' * 8)


def client_auth(body=b'synthetic opaque ticket for wire tests'):
    prefix = struct.pack('<I', 10 + len(body)) + b'\xab\x82' + body
    digest = hashlib.sha1(HELLO[8:] + ACK + prefix).digest()
    prk = hmac.digest(digest, SESSION_KEY, 'sha1')
    challenge = HKDFExpand(hashes.SHA1(), 16, b'CLIENTCHAL').derive(prk)
    keys = HKDFExpand(hashes.SHA1(), 72, b'BDDATA').derive(prk)
    return prefix + challenge[:8], challenge[8:], keys


def request(keys, service=10, task=7, sequence=1, inner=0x86,
            task_tag=3, declared_size=None, filename='motd.txt', parameters=None):
    parameters = b'\x10' + filename.encode('utf-8') + b'\0' if parameters is None else parameters
    payload = bytes((service, task_tag, task)) + parameters
    length = len(payload) if declared_size is None else declared_size
    clear = struct.pack('<IB', length, inner) + payload
    clear += bytes(-len(clear) % 16)
    iv = bytes(range(16))
    aes = Cipher(algorithms.AES(keys[40:56]), modes.CBC(iv)).encryptor()
    encrypted = aes.update(clear) + aes.finalize()
    packet = struct.pack('<I', 30 + len(encrypted)) + b'\xab\x85'
    packet += struct.pack('<I', sequence) + iv + encrypted
    return packet + hmac.digest(keys[:20], packet, 'sha1')[:8]


class MemorySocket:
    def __init__(self, incoming, chunk_size=65536):
        self.incoming = bytearray(incoming)
        self.chunk_size = chunk_size
        self.sent = []

    def recv(self, size):
        size = min(size, self.chunk_size, len(self.incoming))
        data = bytes(self.incoming[:size])
        del self.incoming[:size]
        return data

    def sendall(self, data):
        self.sent.append(bytes(data))


class LobbyTests(unittest.TestCase):
    def test_local_lobby_serves_the_single_killhouse_entry(self):
        import local_server
        class AcceptedSocket(MemorySocket):
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def settimeout(self, _): pass
        auth,_,keys=client_auth()
        parameters=b'\x10\0\x10mp_playlists_shipRetail_release.info\0\0'
        sock=AcceptedSocket(HELLO+auth+request(keys,task=21,parameters=parameters))
        with tempfile.TemporaryDirectory() as temp, patch.object(local_server,'RUNTIME',Path(temp)), \
                patch.object(local_server,'record'), patch.object(local_server,'save_capture',return_value='memory'):
            local_server.lobby_client(sock,('127.0.0.1',40000))
        packet=sock.sent[-1]
        aes=Cipher(algorithms.AES(keys[56:72]),modes.CBC(packet[10:26])).decryptor()
        clear=aes.update(packet[26:-8])+aes.finalize()
        payload=clear[5:5+struct.unpack_from('<I',clear)[0]]
        playlist=payload[32:].decode('ascii')
        self.assertIn('mp_killhouse_sh,ffa,1',playlist)
        self.assertIn('script dm',playlist)
        self.assertEqual(sum(line.startswith('playlist ') for line in playlist.splitlines()),1)

    def test_named_publisher_content_is_returned_exactly_and_other_files_stay_empty(self):
        auth, _, keys = client_auth()
        name = 'mp_playlists_shipRetail_release.info'
        # Transport fixture, not a claim about the playlist parser's text format.
        content = b'local playlist\x00\xff'
        for task, filename in [(21, name), (7, name), (21, 'broadcast.info'), (21, '../' + name)]:
            with self.subTest(task=task, filename=filename):
                parameters = (b'\x10\0' if task == 21 else b'') + b'\x10' + filename.encode() + b'\0\0'
                sock = MemorySocket(HELLO + auth + request(keys, task=task, parameters=parameters))
                handle_lobby(sock, ('127.0.0.1', 40000), lambda *a, **k: None,
                             lambda *_: 'memory', publisher_files={name: content})
                packet = sock.sent[-1]
                self.assertEqual(packet[-8:], hmac.digest(keys[20:40], packet[:-8], 'sha1')[:8])
                aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(packet[10:26])).decryptor()
                clear = aes.update(packet[26:-8]) + aes.finalize()
                payload = clear[5:5 + struct.unpack_from('<I', clear)[0]]
                expected = content if filename == name else b''
                self.assertEqual(payload[16:26], bytes.fromhex('08010000000801000000'))
                self.assertEqual(payload[26:32], b'\x13\x08' + struct.pack('<I', len(expected)))
                self.assertEqual(payload[32:], expected)

    def run_wire(self, wire, chunk_size=65536):
        sock = MemorySocket(wire, chunk_size)
        events, captures = [], []

        def save_capture(kind, data):
            captures.append((kind, bytes(data)))
            return f'memory:{len(captures)}'

        handle_lobby(sock, ('127.0.0.1', 40000),
                     lambda kind, **fields: events.append((kind, fields)), save_capture)
        return sock.sent, events, captures

    def assert_reply(self, packet, keys, task, transaction=1, sequence=1, publisher_file=True):
        self.assertEqual(struct.unpack_from('<I', packet)[0], len(packet) - 4)
        self.assertEqual(packet[4:6], b'\xab\x85')
        self.assertEqual(struct.unpack_from('<I', packet, 6)[0], sequence)
        self.assertEqual(packet[-8:], hmac.digest(keys[20:40], packet[:-8], 'sha1')[:8])
        aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(packet[10:26])).decryptor()
        clear = aes.update(packet[26:-8]) + aes.finalize()
        expected = b'\x0a' + struct.pack('<Q', transaction)
        expected += b'\x08\0\0\0\0\x03' + bytes((task,))
        if publisher_file:
            expected += bytes.fromhex('08010000000801000000130800000000')
        else:
            expected += b'\x08\0\0\0\0'
        self.assertEqual(len(expected), 32 if publisher_file else 21)
        self.assertEqual(clear[:5], struct.pack('<IB', len(expected), 1))
        self.assertEqual(clear[5:5 + len(expected)], expected)
        self.assertEqual(clear[5 + len(expected):], bytes(len(clear) - 5 - len(expected)))

    def test_real_hello_fragmented_bytewise_and_publisher_reply(self):
        auth, proof, keys = client_auth()
        sent, events, captures = self.run_wire(HELLO + auth + request(keys), 1)
        self.assertEqual(SESSION_KEY, bytes.fromhex('1337' * 12))
        self.assertEqual(sent[:2], [ACK, b'\x0a\0\0\0\xab\x83' + proof])
        self.assert_reply(sent[2], keys, 7)
        self.assertFalse([x for x in events if x[0] == 'lobby_error'])
        self.assertTrue(any(kind == 'lobby-request' and data == HELLO
                            for kind, data in captures))
        tasks = [fields for kind, fields in events if kind == 'lobby_task']
        self.assertEqual((tasks[0]['service_id'], tasks[0]['task_id']), (10, 7))
        self.assertEqual(tasks[0]['operation'], 'bdStorage.getPublisherFile')
        self.assertEqual(tasks[0]['filename'], 'motd.txt')
        self.assertEqual(tasks[0]['result_count'], 1)

    def test_codol_task21_publisher_request_with_context(self):
        # Actual client sequence31 at 2026-10-14T03:57:16: context, filename, terminator.
        parameters = bytes.fromhex('100010636f6e666967735f732e696e666f0000')
        auth, _, keys = client_auth()
        sent, events, _ = self.run_wire(HELLO + auth + request(keys, task=21, parameters=parameters))
        self.assert_reply(sent[2], keys, 21)
        task = next(fields for kind, fields in events if kind == 'lobby_task')
        self.assertEqual(task['filename'], 'configs_s.info')
        self.assertEqual(task['result_count'], 1)

    def test_coalesced_packets_echo_unknown_task_and_keepalive(self):
        auth, proof, keys = client_auth()
        wire = bytes(4) + HELLO + auth + request(keys)
        wire += request(keys, service=99, task=201, sequence=2) + bytes(4)
        sent, events, _ = self.run_wire(wire)
        self.assertEqual(sent[0], bytes(4))
        self.assertEqual(sent[1:3], [ACK, b'\x0a\0\0\0\xab\x83' + proof])
        self.assert_reply(sent[3], keys, 7)
        self.assert_reply(sent[4], keys, 201, transaction=2, sequence=2, publisher_file=False)
        self.assertEqual(sent[5], bytes(4))
        self.assertFalse([x for x in events if x[0] == 'lobby_error'])

    def test_length_200_is_special_only_for_initial_hello(self):
        auth, proof, _ = client_auth(bytes(190))
        self.assertEqual(auth[:4], b'\xc8\0\0\0')
        sent, _, _ = self.run_wire(HELLO + auth, 3)
        self.assertEqual(sent, [ACK, b'\x0a\0\0\0\xab\x83' + proof])

    def test_bad_client_proof_is_not_acknowledged(self):
        auth, _, _ = client_auth()
        sent, events, _ = self.run_wire(HELLO + auth[:-1] + bytes((auth[-1] ^ 1,)))
        self.assertEqual(sent, [ACK])
        self.assertTrue(any(kind == 'lobby_error' and 'proof' in fields['error']
                            for kind, fields in events))

    def test_bad_packet_mac_is_not_answered(self):
        auth, _, keys = client_auth()
        packet = request(keys)
        sent, events, _ = self.run_wire(HELLO + auth + packet[:-1] + bytes((packet[-1] ^ 1,)))
        self.assertEqual(len(sent), 2)
        self.assertTrue(any(kind == 'lobby_error' and 'MAC' in fields['error']
                            for kind, fields in events))

    def test_malformed_task_and_unknown_inner_type_are_not_invented(self):
        auth, _, keys = client_auth()
        for kwargs in ({'task_tag': 4}, {'inner': 0x87}, {'declared_size': 999}):
            with self.subTest(kwargs=kwargs):
                sent, events, _ = self.run_wire(HELLO + auth + request(keys, **kwargs))
                self.assertEqual(len(sent), 2)
                self.assertTrue(any(kind == 'lobby_error' for kind, _ in events))

    def test_connection_counters_restart(self):
        auth, _, keys = client_auth()
        for _ in range(2):
            sent, _, _ = self.run_wire(HELLO + auth + request(keys))
            self.assert_reply(sent[-1], keys, 7)

    def test_publisher_filenames_all_return_one_empty_file(self):
        auth, _, keys = client_auth()
        for filename in ('playlists.aggr', 'unknown/publisher-file.bin', ''):
            with self.subTest(filename=filename):
                sent, events, _ = self.run_wire(HELLO + auth + request(keys, filename=filename))
                self.assert_reply(sent[-1], keys, 7)
                task = next(fields for kind, fields in events if kind == 'lobby_task')
                self.assertEqual(task['filename'], filename)

    def test_storage_task3_is_not_misidentified_as_publisher_file(self):
        auth, _, keys = client_auth()
        sent, events, _ = self.run_wire(HELLO + auth + request(keys, task=3))
        self.assert_reply(sent[-1], keys, 3, publisher_file=False)
        task = next(fields for kind, fields in events if kind == 'lobby_task')
        self.assertEqual(task['operation'], 'unimplemented')

    def test_truncated_and_oversized_input_is_recorded(self):
        for wire in (HELLO[:2], HELLO[:-1], HELLO + struct.pack('<I', 0x80001),
                     HELLO + b'\x0a\0\0\0\xab\x82'):
            with self.subTest(wire=wire.hex()):
                _, events, _ = self.run_wire(wire)
                self.assertTrue(any(kind == 'lobby_error' for kind, _ in events))

    def test_wrong_protocol_version_is_not_negotiated(self):
        wire = HELLO[:8] + struct.pack('<II', 220, 220) + HELLO[16:]
        sent, events, _ = self.run_wire(wire)
        self.assertEqual(sent, [])
        self.assertTrue(any(kind == 'lobby_error' for kind, _ in events))


class StunTests(unittest.TestCase):
    def test_demonware_address_reply_has_little_endian_port(self):
        self.assertEqual(stun_reply(b'\x1e\x02\0', ('127.0.0.1', 3074)),
                         bytes.fromhex('1f02007f000001020c'))

    def test_demonware_nat_reply_contains_both_endpoints(self):
        self.assertEqual(stun_reply(b'\x14\x02\0', ('127.0.0.1', 40000),
                                    ('127.0.0.2', 3074)),
                         bytes.fromhex('1502007f000001409c7f000002020c'))

    def test_unknown_and_short_stun_are_unhandled(self):
        for packet in (b'', b'\x1e', b'\x1e\x02', b'\x63\x02\0'):
            self.assertIsNone(stun_reply(packet, ('127.0.0.1', 3074)))


if __name__ == '__main__':
    unittest.main()
