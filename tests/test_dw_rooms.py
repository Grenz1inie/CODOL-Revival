"""Room message wire contract from REA 0xa3d5a0 / 0xa42db0 / 0xa43ba0."""
import hmac
from pathlib import Path
import struct
import tempfile
import unittest

from test_dw_lobby import HELLO, MemorySocket, client_auth, request
from dw_lobby import handle_lobby
from dw_profiles import ProfileStore
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

UID = 0xe94a180c65d3c23b
# Actual 11/4 payload from the first story start. Channel zero is what the
# previous empty create-channel reply left in the client, not a valid allocation.
CAPTURED = bytes.fromhex('0a00000000000000001308220000001e000000020400000028000000e068ab5bab63ab0300003000000040200000000000080100000000')


class RoomWireTests(unittest.TestCase):
    def run_session(self, parameters, owner=True, create=False):
        auth, _, keys = client_auth()
        wire = HELLO + auth
        if owner:
            wire += request(keys, service=8, task=1, parameters=b'\x0a' + struct.pack('<Q', UID) + b'\0')
        if create:
            wire += request(keys, service=11, task=13, parameters=b'\0')
        for sequence, data in enumerate(parameters, 2):
            wire += request(keys, service=11, task=4, sequence=sequence, parameters=data)
        sock, events = MemorySocket(wire, 17), []
        with tempfile.TemporaryDirectory() as folder:
            handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                         lambda *_: 'memory', profiles=ProfileStore(Path(folder)))
        clear = []
        for sequence, packet in enumerate(sock.sent[2:], 1):
            self.assertEqual(struct.unpack_from('<I', packet)[0], len(packet) - 4)
            self.assertEqual(struct.unpack_from('<I', packet, 6)[0], sequence)
            self.assertEqual(packet[-8:], hmac.digest(keys[20:40], packet[:-8], 'sha1')[:8])
            aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(packet[10:26])).decryptor()
            data = aes.update(packet[26:-8]) + aes.finalize()
            clear.append((data[4], data[5:5 + struct.unpack_from('<I', data)[0]]))
        return clear, events

    def test_create_channel_returns_deserializable_info_and_routes_its_message(self):
        message = b'\x0a' + struct.pack('<Q', 1) + CAPTURED[9:]
        replies, events = self.run_session([message], create=True)
        # REA 0xa55a40: u64, u32, u32, u64, bool, bool, u32.
        expected = b'\x0a' + struct.pack('<Q', 1)
        expected += (b'\x08' + struct.pack('<I', 1)) * 2
        expected += b'\x0a' + struct.pack('<Q', UID) + b'\x01\0\x01\0\x08\0\0\0\0'
        self.assertEqual(replies[1][1][16:], (b'\x08\x01\0\0\0' * 2) + expected)
        self.assertEqual([kind for kind, _ in replies], [1, 1, 1, 2])
        self.assertTrue(replies[3][1].endswith(message[:-1]))
        self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))

    def test_channel_creation_without_owner_is_rejected(self):
        replies, events = self.run_session([], owner=False, create=True)
        self.assertEqual(replies, [])
        self.assertTrue(any(kind == 'lobby_error' for kind, _ in events))

    def test_room_broadcast_delivers_exact_message_to_same_local_member(self):
        replies, events = self.run_session([CAPTURED, CAPTURED])
        # One profile reply, then one task acknowledgement + one push each time.
        self.assertEqual([kind for kind, _ in replies], [1, 1, 2, 1, 2])
        expected = b'\x08' + struct.pack('<I', 8)  # push event 8, same consumer as 7
        expected += b'\x0a' + struct.pack('<Q', UID) + b'\x10\0'
        expected += CAPTURED[:-1]  # channel uint64, blob, message-type uint32
        self.assertEqual(replies[2][1], expected)
        self.assertEqual(replies[4][1], expected)
        # Push frames consume sequence numbers, not task transaction IDs.
        self.assertEqual(struct.unpack_from('<Q', replies[3][1], 1)[0], 3)
        self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))

    def test_invalid_room_message_or_unknown_sender_never_emits_push(self):
        malformed = [CAPTURED[:9], b'\x08' + CAPTURED[1:],
                     CAPTURED[:11] + struct.pack('<I', 1025) + CAPTURED[15:],
                     CAPTURED[:-1], CAPTURED + b'\0']
        for parameters, owner in [(data, True) for data in malformed] + [(CAPTURED, False)]:
            with self.subTest(parameters=parameters.hex(), owner=owner):
                replies, events = self.run_session([parameters], owner=owner)
                self.assertFalse(any(kind == 2 for kind, _ in replies))
                self.assertTrue(any(kind == 'lobby_error' for kind, _ in events))
