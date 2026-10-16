"""Single-player booking: real profile export, encrypted lobby, actual client routing."""
from pathlib import Path
import base64
import struct
import tempfile
import unittest
from types import SimpleNamespace

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from client_matchmaking423 import ClientMatchmaking423
from games.codol.versions.v3_3_3_3.server.dw_lobby import handle_lobby
from games.codol.versions.v3_3_3_3.server.dw_matchmaking import StoryMatchmaking
from games.codol.versions.v3_3_3_3.server.dw_profiles import ProfileStore
from games.codol.versions.v3_3_3_3.server.dw_progression import PrivateProfileStore
from test_dw_lobby import HELLO, MemorySocket, client_auth, request
from test_dw_progression import CAPTURE_V19, USER_ID

QUERY = bytes.fromhex('08010000000800000000080a000000079b1ff0d600')


def message(recipient, text):
    inner = struct.pack('<I', len(text)) + text
    return b'\x0a'+struct.pack('<Q', recipient)+b'\x13\x08'+struct.pack('<I', len(inner))+inner+b'\0'


class BookingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.profiles = PrivateProfileStore(self.root/'private', self.root/'backups')
        self.profiles.save(USER_ID, CAPTURE_V19)
        self.native = SimpleNamespace(ready=True, port=28970)
        self.service = StoryMatchmaking(self.native, self.profiles, self.root/'instance')

    def book(self, sid=None, recipient=None):
        sid = base64.b64encode(self.service.security_id).decode() if sid is None else sid
        return message(recipient or self.service.server_id, f'mmbook 1 {sid} 0'.encode())

    def test_ready_candidate_exports_profile_and_admission_before_booking_ack(self):
        service = self.service
        candidate, = service.find(USER_ID, QUERY)
        client = ClientMatchmaking423()
        ok, obj, used = client.candidate(candidate)
        self.assertTrue(ok)
        self.assertEqual(used, len(candidate))
        self.assertEqual(obj[0x10:0x18], service.security_id)
        self.assertEqual(obj[0x1cc:0x1dc], service.security_key)
        self.assertTrue((service.profile_path/f'mpdata_s.{USER_ID}').is_file())
        roster = service.admission_path.read_text().split()
        self.assertEqual(roster[:3], ['127.0.0.1', service.security_key.hex(), f'{USER_ID:016x}'])
        for _ in range(2):  # Retry has the same reservation and key.
            push = service.message(USER_ID, self.book())
            self.assertEqual(client.booking_push(push), (service.server_id, b'mmbook accepted'))
        self.assertIsNone(service.message(USER_ID, message(service.server_id,
                          b'mmstart sv_resetServer; map mp_cargoship;')))
        self.assertIsNone(service.message(USER_ID, message(service.server_id,
                          b'mmstart sv_resetServer; g_gametype coop; map coop_training_mp_cargoship;')))
        self.assertEqual((self.profiles.directory/f'{USER_ID:016x}.bin').read_bytes(), CAPTURE_V19)

    def test_not_ready_missing_profile_or_another_owner_never_publishes(self):
        self.native.ready = False
        self.assertEqual(self.service.find(USER_ID, QUERY), ())
        self.assertFalse(self.service.admission_path.exists())
        with self.assertRaises(ValueError):
            self.service.message(USER_ID, self.book())
        self.native.ready = True
        with self.assertRaises(ValueError):
            self.service.find(123, QUERY)
        self.service.find(USER_ID, QUERY)
        with self.assertRaises(ValueError):
            self.service.find(USER_ID+1, QUERY)
        self.native.ready = False
        with self.assertRaises(ValueError):
            self.service.message(USER_ID, self.book())

    def test_invalid_query_message_identity_and_other_maps_are_rejected(self):
        for bad in (QUERY[:-1], QUERY+b'\0', b'\x07'+QUERY[1:]):
            with self.subTest(query=bad.hex()), self.assertRaises(ValueError):
                self.service.find(USER_ID, bad)
        self.service.find(USER_ID, QUERY)
        valid = self.book()
        for bad in (valid[:-1], valid+b'\0', self.book(sid='00'*8), self.book(recipient=42),
                    message(self.service.server_id, b'mmstart map mp_rust;'),
                    message(self.service.server_id, b'mmstart map mp_cargoship; map mp_rust;'),
                    message(self.service.server_id, b'quit'),
                    message(self.service.server_id, b'mmbook 1 bad 0')):
            with self.subTest(message=bad.hex()), self.assertRaises(ValueError):
                self.service.message(USER_ID, bad)
        with self.assertRaises(ValueError):
            self.service.message(USER_ID+1, valid)

    def test_encrypted_find_and_book_return_candidate_then_task_ack_then_event21(self):
        auth, _, keys = client_auth()
        wire = HELLO+auth+request(keys, service=8, task=1,
                                 parameters=b'\x0a'+struct.pack('<Q', USER_ID)+b'\0')
        wire += request(keys, service=21, task=5, parameters=QUERY)
        wire += request(keys, service=6, task=14, parameters=self.book())
        sock, events = MemorySocket(wire, 17), []
        handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                     lambda *_: 'memory', profiles=ProfileStore(self.root/'public'), matchmaking=self.service)
        clear = []
        for packet in sock.sent[2:]:
            decryptor = Cipher(algorithms.AES(keys[56:72]), modes.CBC(packet[10:26])).decryptor()
            data = decryptor.update(packet[26:-8])+decryptor.finalize()
            clear.append((data[4], data[5:5+struct.unpack_from('<I', data)[0]]))
        self.assertFalse([entry for entry in events if entry[0] == 'lobby_error'], events)
        self.assertEqual([kind for kind, _ in clear], [1, 1, 1, 2])
        client = ClientMatchmaking423()
        self.assertTrue(client.candidate(clear[1][1][26:])[0])
        self.assertEqual(client.booking_push(clear[3][1]), (self.service.server_id, b'mmbook accepted'))
