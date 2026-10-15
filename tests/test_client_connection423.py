import struct
import unittest
from client_connection423 import ClientConnection423


class CurrentConnectionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientConnection423()

    def test_current_tiger_matches_standard_empty_digest(self):
        self.assertEqual(self.client.tiger(b'').hex(), '3293ac630c13f0245f92bbb1766e16167a4e58492dde73f3')

    def test_current_stats_writer_uses_total_length_without_qport(self):
        packed = bytes(range(256))*10
        for index in range(3):
            with self.subTest(index=index):
                self.assertEqual(self.client.stats_fragment(packed, index),
                                 struct.pack('<BH', index, len(packed))+packed[index*1238:(index+1)*1238])

    def test_current_raw_stats_has_27_fragments_and_580_byte_tail(self):
        raw = bytes(range(256))*128
        self.assertEqual(self.client.stats_fragment(raw, 26, compressed=False),
                         b'\x1a\0\0'+raw[26*1238:])
