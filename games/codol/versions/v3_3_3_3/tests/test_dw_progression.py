"""Private profile wire/persistence contract, grounded in the live v19 schema."""
from pathlib import Path
import base64
import hashlib
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / 'src'))
from games.codol.versions.v3_3_3_3.server.dw_progression import PrivateProfileStore
from games.codol.versions.v3_3_3_3.server.dw_profiles import ProfileError, validate_profile
from games.codol.versions.v3_3_3_3.server.dw_lobby import handle_lobby
from test_dw_lobby import HELLO, MemorySocket, client_auth, request
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

USER_ID = 0xe94a180c65d3c23b

# Existing v19 backup 20261014T074245316871-e94a180c65d3c23b.bin.
# Wire SHA256: dc7e11a3f636768ee1122806375bcf2ad79fbcfeab77b59f16f9dd6af8ddff34.
# Keep the captured compression, CRC and extension bytes unchanged.
CAPTURE_V19 = base64.b64decode(
    'CAEAAAAIAQAAAAhWKpOfEwhrAAAAeJztzrENQFAYhdE/odRpzKBT6xUGsIHCEBZ4rQHsYgVT2MKb'
    'QRQi5yRfeZM7tdteR8SydikAAAAA4P+K3JArH2yrZrz645xfvgQAAAAAAAAAAAAAAAAAAAAAAAAA'
    'AAAAAAAAAHzBDdUIB0AHAAAAAAcAAAAABwAAAAAHAAAAAAcAAAAABwAAAAAHAAAAAAcAAAAABwAA'
    'AAAHAAAAAAcAAAAABwAAAAAHAAAAAAcAAAAABwAAAAANAAAAAAcAAAAABwAAAAAHAwAAAAdGAAAA'
    'BwQAAAAHAAAAAAcAAAAABwAAAAAHAAAAAAcAAAAABwAAAAAHAAAAAAcAAAAABwAAAAAHAAAAAAcA'
    'AAAABwAAAAAHAAAAAAcAAAAADQAAAAAA'
)
NATIVE_V19_SHA256 = 'b334ca17c875340466bb41feea611dc99439e45d1527d4223f016dcd19f25034'
RAW_V19_SHA256 = 'd8bbaa4f6aeeb76dcc8646af7a2aca528900e6dd3a75185f6e5baaeef62a6a3f'


class ProgressionTests(unittest.TestCase):
    def test_story_unlock_changes_only_captured_prerequisites_and_survives_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            data, backups = Path(directory) / 'data', Path(directory) / 'backups'
            store = PrivateProfileStore(data, backups)
            store.set_progression(USER_ID, 70, 3)
            before = store.load(USER_ID)
            original = validate_profile(before[9:] + b'\0')
            store.unlock_story(USER_ID)
            store = PrivateProfileStore(data, backups)
            after = store.load(USER_ID)
            raw = validate_profile(after[9:] + b'\0')
            # Live v19 offsets for unlockFlagsNew[150..159], including CRC prefix.
            expected = bytearray(original)
            for offset in (8595, 8597, 8599, 8601, 8603, 8605, 8607, 8609, 8611, 8613):
                struct.pack_into('<H', expected, offset, 1)
            self.assertEqual(raw[4:], expected[4:])
            self.assertEqual(store.summary(USER_ID), {'level': 70, 'prestige': 3})
            self.assertIn(before[9:] + b'\0', [p.read_bytes() for p in backups.glob('*.bin')])
            store.unlock_story(USER_ID)
            self.assertEqual(store.load(USER_ID), after)

    def test_story_unlock_refuses_missing_and_corrupt_private_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / 'data'
            store = PrivateProfileStore(data, Path(directory) / 'backups')
            with self.assertRaises(ValueError):
                store.unlock_story(USER_ID)
            self.assertFalse(data.exists())
            data.mkdir()
            path = data / f'{USER_ID:016x}.bin'
            path.write_bytes(b'corrupt')
            with self.assertRaises(ValueError):
                store.unlock_story(USER_ID)
            self.assertEqual(path.read_bytes(), b'corrupt')

    def test_private_fetch_and_save_round_trip_through_encrypted_lobby(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PrivateProfileStore(Path(directory) / 'data', Path(directory) / 'backups')
            store.set_progression(USER_ID, 70, 3)
            expected_profile = store.load(USER_ID)
            auth, _, keys = client_auth()
            lookup = b'\x0a' + struct.pack('<Q', USER_ID) + b'\0'
            from games.codol.versions.v3_3_3_3.server.dw_profiles import ProfileStore
            public = ProfileStore(Path(directory) / 'public')
            events = []
            sock = MemorySocket(HELLO + auth + request(keys, service=8, task=1, parameters=lookup)
                                + request(keys, service=8, task=6, sequence=2, parameters=expected_profile + b'\0')
                                + request(keys, service=8, task=2, sequence=3, parameters=b'\0'))
            handle_lobby(sock, ('127.0.0.1', 40000), lambda kind, **data: events.append((kind, data)),
                         lambda *_: 'memory', profiles=public, private_profiles=store)
            reply = sock.sent[-1]
            aes = Cipher(algorithms.AES(keys[56:72]), modes.CBC(reply[10:26])).decryptor()
            clear = aes.update(reply[26:-8]) + aes.finalize()
            self.assertIn(expected_profile, clear)
            self.assertEqual([e['result_count'] for kind, e in events if kind == 'lobby_task'], [0, 0, 1])
            self.assertFalse(any(kind == 'lobby_error' for kind, _ in events))
            self.assertTrue(list((Path(directory) / 'backups').glob('*.bin')))

    def test_corrupt_profile_is_not_overwritten_and_unrelated_bytes_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            store = PrivateProfileStore(Path(directory) / 'data', Path(directory) / 'backups')
            store.set_progression(USER_ID, 1, 0)
            original = store.load(USER_ID)[9:] + b'\0'
            for damaged in [original[:80], original[:-6] + b'\0', original[:11] + bytes([original[11] ^ 1]) + original[12:]]:
                with self.assertRaises(ValueError):
                    store.save(USER_ID, damaged)
                self.assertEqual(store.load(USER_ID)[9:] + b'\0', original)
            raw = bytearray(validate_profile(original))
            raw[17000:17004] = b'keep'
            crc = zlib.crc32(raw[4:])
            struct.pack_into('<I', raw, 0, crc)
            packed = zlib.compress(raw)
            old_length = struct.unpack_from('<I', original, 17)[0]
            edited = original[:11] + struct.pack('<I', crc) + b'\x13\x08' + struct.pack('<I', len(packed)) + packed + original[21 + old_length:]
            store.save(USER_ID, edited)
            store.set_progression(USER_ID, 70, 3)
            self.assertEqual(validate_profile(store.load(USER_ID)[9:] + b'\0')[17000:17004], b'keep')

    def test_max_progression_reloads_backs_up_and_rejects_out_of_range_values(self):
        with tempfile.TemporaryDirectory() as directory:
            data, backups = Path(directory) / 'data', Path(directory) / 'backups'
            store = PrivateProfileStore(data, backups)
            self.assertIsNone(store.load(USER_ID))
            store.set_progression(USER_ID, 1, 0)
            before = store.load(USER_ID)
            # Captured unlockFlags.csv maps uf_prestige_rank to index 1;
            # private schema slot 7446 has byte offset 8293, plus CRC prefix 4.
            self.assertEqual(struct.unpack_from('<H', validate_profile(before[9:] + b'\0'), 8297)[0], 1)
            store.set_progression(USER_ID, 70, 3)
            store = PrivateProfileStore(data, backups)
            self.assertEqual(store.summary(USER_ID), {'level': 70, 'prestige': 3})
            wire = store.load(USER_ID)[9:] + b'\0'
            raw = validate_profile(wire)
            self.assertEqual(struct.unpack_from('<II', raw, 4), (19, 2318499177))
            # Offsets and extension positions come from live-player-schema.json.
            self.assertEqual(struct.unpack_from('<iii', raw, 4883), (3, 70, 4))
            self.assertEqual(struct.unpack_from('<i', raw, 4844)[0], 0)
            self.assertEqual(struct.unpack_from('<H', raw, 8297)[0], 370)
            length = struct.unpack_from('<I', wire, 17)[0]
            extension = wire[21 + length:-1]
            self.assertEqual(len(extension), 180)
            self.assertEqual(extension[90:105], bytes.fromhex('070300000007460000000704000000'))
            self.assertEqual(extension[75], 13)  # kills is float, not int32.
            self.assertEqual(extension[175], 13)  # wins is float.
            self.assertEqual(next(backups.glob('*.bin')).read_bytes(), before[9:] + b'\0')
            saved = store.load(USER_ID)
            for level, prestige in [(0, 3), (71, 3), (70, -1), (70, 4), (True, 3), (70, 3.0)]:
                with self.subTest(level=level, prestige=prestige), self.assertRaises(ValueError):
                    store.set_progression(USER_ID, level, prestige)
                self.assertEqual(store.load(USER_ID), saved)


class NativeProfileExportTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='codol-profile-export-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.store = PrivateProfileStore(self.root / 'data', self.root / 'backups')
        self.store.save(USER_ID, CAPTURE_V19)
        self.source = self.store.directory / f'{USER_ID:016x}.bin'

    def test_export_preserves_captured_v19_zlib_and_source(self):
        before = self.source.stat()
        destination = self.root / 'instance' / 'profiles'
        result = self.store.export_native(USER_ID, destination)
        self.assertEqual(result, destination / 'mpdata_s.16810275000640848443')
        self.assertEqual(len(result.read_bytes()), 107)
        self.assertEqual(hashlib.sha256(result.read_bytes()).hexdigest(), NATIVE_V19_SHA256)
        self.assertEqual(self.source.read_bytes(), CAPTURE_V19)
        self.assertEqual(self.source.stat().st_mtime_ns, before.st_mtime_ns)
        self.assertFalse(self.store.backups.exists())
        self.assertEqual(list(destination.iterdir()), [result])

    def test_export_replaces_only_selected_uid_file(self):
        destination = self.root / 'profiles'
        destination.mkdir()
        target = destination / f'mpdata_s.{USER_ID}'
        target.write_bytes(b'previous profile')
        other = destination / 'mpdata_s.1'
        other.write_bytes(b'other player')
        self.assertEqual(self.store.export_native(USER_ID, str(destination)), target)
        self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), NATIVE_V19_SHA256)
        self.assertEqual(other.read_bytes(), b'other player')
        self.assertEqual(self.source.read_bytes(), CAPTURE_V19)
        self.assertEqual(set(destination.iterdir()), {target, other})

    def assert_export_rejected(self, user_id, message):
        original = self.source.read_bytes() if self.source.exists() else None
        for existing in (False, True):
            with self.subTest(existing=existing):
                destination = self.root / ('existing' if existing else 'absent')
                target = destination / f'mpdata_s.{user_id}'
                if existing:
                    destination.mkdir(exist_ok=True)
                    target.write_bytes(b'keep previous export')
                before = {p.name: p.read_bytes() for p in destination.iterdir()} if existing else {}
                with self.assertRaisesRegex(ProfileError, message):
                    self.store.export_native(user_id, destination)
                if existing:
                    self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, before)
                else:
                    self.assertFalse(destination.exists())
                self.assertEqual(self.source.read_bytes() if self.source.exists() else None, original)

    def test_export_rejects_invalid_uid_without_writes(self):
        for user_id in (None, False, True, 0, -1, 1 << 64, 1.0, str(USER_ID)):
            with self.subTest(user_id=user_id):
                self.assert_export_rejected(user_id, 'UID')

    def test_export_rejects_bad_length_and_crc_without_writes(self):
        # The compressed segment is exactly bytes 21..127 in this capture.
        bad_crc = CAPTURE_V19[:11] + bytes([CAPTURE_V19[11] ^ 1]) + CAPTURE_V19[12:]
        raw = bytearray(zlib.decompress(CAPTURE_V19[21:128]))
        raw[17000] ^= 1
        packed = zlib.compress(raw)
        damaged = {
            'short length': CAPTURE_V19[:17] + struct.pack('<I', 106) + CAPTURE_V19[21:],
            'oversized length': CAPTURE_V19[:17] + struct.pack('<I', 1000) + CAPTURE_V19[21:],
            'trailing compressed byte': CAPTURE_V19[:17] + struct.pack('<I', 108)
                + CAPTURE_V19[21:128] + b'\0' + CAPTURE_V19[128:],
            'envelope CRC': bad_crc,
            'record CRC': CAPTURE_V19[:17] + struct.pack('<I', len(packed)) + packed + CAPTURE_V19[128:],
        }
        for name, wire in damaged.items():
            with self.subTest(damage=name):
                self.source.write_bytes(wire)
                self.assert_export_rejected(USER_ID, '')

    def test_export_rejects_missing_profile_without_writes(self):
        self.source.unlink()
        self.assert_export_rejected(USER_ID, 'not found')


if __name__ == '__main__':
    unittest.main()
