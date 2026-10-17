import hashlib
import struct
import unittest
import zlib
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import padding, rsa
from games.codol.versions.v3_19_26_22.client import localization
from games.codol.versions.v3_19_26_22.client.fastfile import crypt


def zone(rows):
    body, index = b'', b''
    for kind, row in rows:
        index += struct.pack('<4I', kind, 16+len(rows)*16+len(body), 0xffffffff, len(row))
        body += row
    result = bytearray(struct.pack('<10I', 16+len(index)+len(body), 0, 0, 0, 0, 1000+len(body), 0, 0, 0, 0))
    return bytes(result) + struct.pack('<4I', 0, 0, len(rows), 0xffffffff) + index + body


class LocalizationTests(unittest.TestCase):
    def test_translation_rebases_shared_strings_and_keeps_other_asset_bytes(self):
        original = zone([(27, b'\xff'*8+b'cn\0FIRST\0'),
                         (27, struct.pack('<II', 0x30000020, 0xffffffff)+b'SECOND\0'),
                         (37, struct.pack('<4I', 0xffffffff, 1, 1, 0xffffffff)+b'table\0'+struct.pack('<II', 0x30000020, 123))])
        expected = zone([(27, b'\xff'*8+b'English\0FIRST\0'),
                         (27, struct.pack('<II', 0x30000025, 0xffffffff)+b'SECOND\0'),
                         (37, struct.pack('<4I', 0xffffffff, 1, 1, 0xffffffff)+b'table\0'+struct.pack('<II', 0x30000025, 123))])
        spec = {'source': hashlib.sha256(original).hexdigest(), 'result': hashlib.sha256(expected).hexdigest(),
                'strings': {'0': 'English'}, 'pointer_deltas': [[0x30000000, 0], [0x30000020, 5]],
                'material_pointers': {}}
        self.assertEqual(localization.translate_zone(original, spec), expected)
        with self.assertRaisesRegex(ValueError, 'source'):
            localization.translate_zone(original+b'bad', spec)
        with self.assertRaisesRegex(ValueError, 'result'):
            localization.translate_zone(original, {**spec, 'pointer_deltas': [[0x30000000, 0]]})

    def test_unsigned_fastfile_encrypts_only_the_initial_io_buffer(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        material = bytes(range(40))
        wrapped = private.public_key().encrypt(material, padding.PKCS1v15())
        template = b'IWff0100'+struct.pack('<I', 461)+b'\0'*9+wrapped+b'\0'*400000
        import random
        data = random.Random(319).randbytes(300000)
        result = localization.unsigned(template, data, private)
        self.assertEqual(len(result), len(template))
        self.assertEqual(result[:8], b'IWffu100')
        clear = crypt(result[277:0x40000], material[:24], material[24:])+result[0x40000:]
        self.assertEqual(zlib.decompress(clear), data)
        with self.assertRaisesRegex(ValueError, 'capacity'):
            localization.unsigned(template[:400], data, private)

    def test_archive_replacement_updates_block_digests_and_rejects_wrong_input(self):
        data = bytearray(0x4000*2)
        data[:4] = b'nifs'
        struct.pack_into('<Q', data, 0x24, len(data))
        struct.pack_into('<I', data, 0x4c, 2)
        data[500:510] = b'oldpayload'
        data += b''.join(hashlib.md5(data[i:i+0x4000]).digest() for i in range(0,len(data),0x4000))+b'\x01'*16
        original = bytes(data)
        with patch.object(localization, 'ARCHIVE_SHA256', hashlib.sha256(original).hexdigest()):
            result = localization.patch_archive(original, [(b'oldpayload', b'newpayload')])
            self.assertEqual(result[500:510], b'newpayload')
            self.assertEqual(result[0x8000:0x8010], hashlib.md5(result[:0x4000]).digest())
            self.assertEqual(result[0x4000:0x8000], original[0x4000:0x8000])
            self.assertEqual(result[0x8010:0x8020], original[0x8010:0x8020])
            self.assertEqual(result[0x8020:0x8030], hashlib.md5(result[0x8000:0x8020]).digest())
            for replacements in ([(b'absent',b'present')], [(b'oldpayload',b'longer payload')]):
                with self.assertRaises(ValueError): localization.patch_archive(original,replacements)
            with self.assertRaisesRegex(ValueError, 'archive'):
                localization.patch_archive(original+b'bad', [])
