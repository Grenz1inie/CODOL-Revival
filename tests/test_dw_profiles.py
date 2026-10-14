"""CODOL profile capture round-trip; all writes stay in a temporary directory."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import hmac

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from dw_profiles import ProfileStore, validate_profile
from dw_lobby import handle_lobby
from test_dw_lobby import HELLO, MemorySocket, client_auth, request

CAPTURE = Path(__file__).resolve().parent / 'fixtures/public-profile.bin'
USER_ID = 0xe94a180c65d3c23b


class ProfileTests(unittest.TestCase):
    def test_real_capture_crc_and_complete_payload(self):
        wire = CAPTURE.read_bytes()
        raw = validate_profile(wire)
        self.assertEqual(len(raw), 32768)
        self.assertEqual(struct.unpack_from('<I', raw)[0], 0xdea7c860)
        self.assertEqual(wire[21 + 1179:-1:5], bytes([7]) * 125)

    def test_save_reload_returns_uid_then_exact_profile_without_terminator(self):
        wire = CAPTURE.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory))
            self.assertIsNone(store.load(USER_ID))
            store.save(USER_ID, wire)
            reloaded = ProfileStore(Path(directory)).load(USER_ID)
            self.assertEqual(reloaded, b'\x0a' + struct.pack('<Q', USER_ID) + wire[:-1])

    def test_bad_checksum_does_not_replace_saved_profile(self):
        wire = CAPTURE.read_bytes()
        broken = bytearray(wire)
        broken[11] ^= 1
        with tempfile.TemporaryDirectory() as directory:
            store = ProfileStore(Path(directory))
            store.save(USER_ID, wire)
            with self.assertRaisesRegex(ValueError, 'CRC32'):
                store.save(USER_ID, broken)
            self.assertEqual(store.load(USER_ID)[9:], wire[:-1])

    def test_truncated_blob_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_profile(CAPTURE.read_bytes()[:200])

    def test_encrypted_save_then_new_connection_read(self):
        wire = CAPTURE.read_bytes()
        lookup = b'\x0a' + struct.pack('<Q', USER_ID) + b'\0'
        auth, _, keys = client_auth()
        with tempfile.TemporaryDirectory() as directory:
            events = []
            def run(tasks):
                sock = MemorySocket(HELLO + auth + b''.join(tasks))
                handle_lobby(sock, ('127.0.0.1', 40000),
                             lambda kind, **data: events.append((kind, data)),
                             lambda *_: 'memory', profiles=ProfileStore(Path(directory)))
                return sock.sent[-1]

            run([request(keys, service=8, task=1, parameters=lookup),
                 request(keys, service=8, task=3, sequence=2, parameters=wire)])
            reply = run([request(keys, service=8, task=1, parameters=lookup)])
            self.assertEqual(reply[-8:], hmac.digest(keys[20:40], reply[:-8], 'sha1')[:8])
            aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(reply[10:26])).decryptor()
            clear = aes.update(reply[26:-8]) + aes.finalize()
            expected = (b'\x0a' + struct.pack('<Q', 1) + b'\x08\0\0\0\0\x03\x01'
                        + b'\x08\x01\0\0\0' * 2 + lookup[:-1] + wire[:-1])
            self.assertEqual(clear[5:5 + len(expected)], expected)
            self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))


if __name__ == '__main__':
    unittest.main()
