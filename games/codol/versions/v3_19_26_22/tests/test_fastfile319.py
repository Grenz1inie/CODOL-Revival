import hashlib
import struct
import unittest
import zlib

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa, utils

from games.codol.versions.v3_19_26_22.client.fastfile import crypt, decode, keys, raw_files


class FastFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public = cls.private.public_key()

    def fixture(self):
        material = bytes(range(40))
        zone = b'original resource contents\0' * 1000
        packed = zlib.compress(zone).ljust(8192, b'\0')
        table = hashlib.sha256(packed).digest().ljust(8192, b'\0')
        header = bytearray(8192)
        header[:8] = b'IWffs100'
        header[300:332] = b'mp_playlists'.ljust(32, b'\0')
        header[336:368] = hashlib.sha256(table).digest()
        header[12:44] = hashlib.sha256(header[300:8144]).digest()
        header[44:300] = self.private.sign(bytes(header[12:44]), padding.PKCS1v15(), utils.Prehashed(hashes.SHA256()))
        wire = b'IWff0100' + struct.pack('<I', 461) + bytes(9)
        wire += self.public.encrypt(material, padding.PKCS1v15())
        wire += crypt(bytes(header), material[:24], material[24:])
        wire += crypt(table, material[:24], header[336:352])
        wire += crypt(packed, material[:24], table[:16])
        return wire, zone

    def test_signed_original_resource_is_verified_and_decompressed(self):
        wire, zone = self.fixture()
        self.assertEqual(decode(wire, 'mp_playlists', self.private, self.public), zone)

    def test_modified_truncated_wrong_version_or_wrong_named_resource_is_rejected(self):
        wire, _ = self.fixture()
        for changed in (wire[:-1], wire[:8]+struct.pack('<I',423)+wire[12:],
                        wire[:290]+bytes([wire[290]^1])+wire[291:],
                        wire[:9000]+bytes([wire[9000]^1])+wire[9001:],
                        wire[:-1]+bytes([wire[-1]^1])):
            with self.subTest(length=len(changed)), self.assertRaises(ValueError):
                decode(changed, 'mp_playlists', self.private, self.public)
        with self.assertRaisesRegex(ValueError, 'name'):
            decode(wire, 'ui_mp', self.private, self.public)
        other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with self.assertRaisesRegex(ValueError, 'signature'):
            decode(wire, 'mp_playlists', self.private, other.public_key())

    def test_wrong_client_cannot_supply_crypto_material(self):
        with self.assertRaisesRegex(ValueError, 'client'):
            keys(b'another version')

    def test_raw_file_uses_asset_lengths_and_checks_decompressed_size(self):
        text = b'version 797\nrule requireOpenNat 1\n'
        packed = zlib.compress(text)
        name = b'mp_playlists.info\0'
        payload = struct.pack('<4I', 0xffffffff, len(packed), len(text), 0xffffffff) + name + packed
        zone = bytearray(40) + struct.pack('<4I', 0, 0, 1, 0xffffffff)
        zone += struct.pack('<4I', 36, 32, 0xffffffff, len(payload)) + payload
        struct.pack_into('<I', zone, 0, len(zone)-40)
        self.assertEqual(raw_files(bytes(zone)), {'mp_playlists.info': text})
        for offset in (0, 40, 56+12, 72+8):
            changed = bytearray(zone)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                raw_files(bytes(changed))
