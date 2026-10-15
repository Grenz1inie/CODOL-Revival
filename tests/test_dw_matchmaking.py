"""Current 21/5 result contract, checked by the shipped client's reader."""
import struct
import unittest

from client_matchmaking423 import ClientMatchmaking423
from dw_matchmaking import server_result


class MatchmakingResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientMatchmaking423()

    def test_local_server_identity_address_and_key_reach_current_consumer(self):
        security_id = bytes.fromhex('1020304050607080')
        key = bytes(range(16))
        wire = server_result(port=28970, server_id=0x3333000000000001,
                             security_id=security_id, security_key=key)
        ok, obj, cursor = self.client.candidate(wire)
        self.assertTrue(ok)
        self.assertEqual(cursor, len(wire))
        self.assertEqual(obj[0x10:0x18], security_id)
        self.assertEqual(obj[0x1cc:0x1dc], key)
        self.assertEqual(struct.unpack_from('<Q', obj, 0x168)[0], 0x3333000000000001)
        self.assertEqual(struct.unpack_from('<I', obj, 0x118)[0], 37)
        # Five local addresses, public address, NAT type; each port is little-endian.
        self.assertEqual(obj[0x18:0x3d], bytes.fromhex('7f0000012a71') + bytes(24)
                         + bytes.fromhex('7f0000012a7101'))
        self.assertEqual(struct.unpack_from('<3I', obj, 0x11c), (0, 1, 0))
        self.assertEqual(obj[0x170:0x17c], b'CODOL Local\0')

    def test_truncated_result_is_rejected_by_current_reader(self):
        wire = server_result(port=28970, server_id=1, security_id=b'12345678',
                             security_key=b'0123456789abcdef')
        for length in (0, 5, 42, 57, len(wire) - 1):
            with self.subTest(length=length):
                ok, _, _ = self.client.candidate(wire[:length])
                self.assertFalse(ok)

    def test_invalid_connection_material_is_not_serialized(self):
        valid = dict(port=28970, server_id=1, security_id=b'12345678',
                     security_key=b'0123456789abcdef')
        for field, value in (('port', 0), ('port', 65536), ('port', True),
                             ('server_id', 0), ('server_id', 1 << 64), ('server_id', True),
                             ('security_id', b'1234567'), ('security_id', b'123456789'),
                             ('security_key', bytes(15)), ('security_key', bytes(17))):
            with self.subTest(field=field, value=value):
                with self.assertRaises(ValueError):
                    server_result(**{**valid, field: value})
