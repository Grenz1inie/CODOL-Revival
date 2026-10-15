"""Connection state tested with the 3.3.3.3 client's own stats writer."""
import hashlib
import struct
import unittest
import zlib

from client_connection423 import ClientConnection423
from client_reader423 import ClientReader423


def profile_bytes():
    data = (hashlib.shake_256(b'independent stats fixture').digest(8000)*5)[:32764]
    return struct.pack('<I', zlib.crc32(data))+data


class StatsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientConnection423()

    def test_current_client_fragments_complete_only_after_all_crc_checked_data(self):
        from match_server.connection import StatsTransfer
        profile = profile_bytes()
        for compressed in (False, True):
            source = zlib.compress(profile) if compressed else profile
            fragments = [self.client.stats_fragment(source, i, compressed=compressed)
                         for i in range((len(source)+1237)//1238)]
            transfer = StatsTransfer()
            missing = (1 << len(fragments))-1
            for i in reversed(range(len(fragments))):
                missing &= ~(1 << i)
                self.assertEqual(transfer.accept(fragments[i]), missing)
                self.assertEqual(transfer.accept(fragments[i]), missing)
                self.assertEqual(transfer.profile, None if missing else profile)

    def test_invalid_fragments_do_not_replace_accepted_fragments(self):
        from match_server.connection import StatsTransfer
        source = zlib.compress(profile_bytes())
        fragments = [self.client.stats_fragment(source, i)
                     for i in range((len(source)+1237)//1238)]
        transfer = StatsTransfer()
        missing = transfer.accept(fragments[0])
        invalid = [b'', fragments[1][:-1], fragments[1]+b'x',
                   bytes([27])+fragments[1][1:],
                   fragments[1][:1]+struct.pack('<H',len(source)-1)+fragments[1][3:],
                   fragments[0][:-1]+bytes([fragments[0][-1]^1])]
        for value in invalid:
            with self.assertRaises(ValueError):
                transfer.accept(value)
            self.assertIsNone(transfer.profile)
            self.assertEqual(transfer.accept(fragments[0]), missing)
        for fragment in fragments[1:]:
            remaining = transfer.accept(fragment)
        self.assertEqual(remaining, 0)
        self.assertEqual(transfer.profile, profile_bytes())

    def test_bad_crc_or_zlib_tail_never_publishes_a_profile(self):
        from match_server.connection import StatsTransfer
        valid = profile_bytes()
        for source in (zlib.compress(b'\0'*32768), zlib.compress(valid)+b'tail',
                       zlib.compress(valid[:-1]), zlib.compress(valid+b'x')):
            transfer = StatsTransfer()
            fragments = [self.client.stats_fragment(source, i)
                         for i in range((len(source)+1237)//1238)]
            for fragment in fragments[:-1]:
                transfer.accept(fragment)
            with self.assertRaises(ValueError):
                transfer.accept(fragments[-1])
            self.assertIsNone(transfer.profile)


class ConnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientConnection423()

    def setUp(self):
        from match_server.connection import Connection
        self.uid = 0x1234567812345678
        self.connection = Connection(self.uid, netconst_checksum=0x11223344)

    def connect(self):
        challenge, = self.connection.receive(b'\xff'*4+f'getchallenge {self.uid:016x}\0'.encode())
        self.challenge = int(challenge[4:].rstrip(b'\0').split()[1])
        self.info = f'\\xuid\\{self.uid:016x}\\challenge\\{self.challenge}\\name\\VGVzdA=='
        self.request = b'\xff'*4+f'connect {self.uid:016x} "{self.info}"\0'.encode()
        reply, = self.connection.receive(self.request)
        self.assertIn(b'connectResponse \\mapname\\mp_killhouse_sh', reply)
        self.assertEqual(self.connection.receive(self.request), [reply])
        self.assertEqual(self.connection.phase, 'connected')

    def upload(self):
        source = zlib.compress(profile_bytes())
        for i in range((len(source)+1237)//1238):
            replies = self.connection.receive(b'\xff'*4+b'stats\0'+self.client.stats_fragment(source, i))
        self.assertEqual(replies, [b'\xff'*4+b'statResponse 0\0'])

    def packet(self, body, sequence, *, ack=0, server_id=255):
        key = (self.challenge ^ server_id ^ ack)&255
        return struct.pack('<IBII', sequence, server_id, ack, 0)+bytes(x^key for x in body)

    def test_admitted_client_receives_current_gamestate_after_valid_stats(self):
        self.connect()
        with self.assertRaisesRegex(ValueError, 'stats'):
            self.connection.receive(self.packet(b'\x03', 1))
        self.upload()
        packets = self.connection.receive(self.packet(b'\x03', 1))
        reader = ClientReader423()
        reader.reset_netchan()
        for packet in packets:
            decoded = reader.packet(packet, challenge=self.challenge)
        sequence, ack, wire = decoded
        self.assertEqual(ack, 0)
        state = reader.gamestate(wire, checksum=0x11223344)
        self.assertEqual((state['map'], state['game_type'], state['client_number']),
                         ('mp_killhouse_sh', 'dm', 0))
        self.assertEqual(self.connection.phase, 'primed')
        self.assertEqual(self.connection.receive(self.packet(b'\x03', 1)), [])
        # Latest userinfo is acknowledged and keys the downstream XOR encoder.
        command = f'userinfo "{self.info}"'.encode()
        packet = self.packet(b'\x1a'+struct.pack('<I',1)+command+b'\0\x03', 2,
                             ack=sequence, server_id=self.connection.server_id)
        replies = self.connection.receive(packet)
        self.assertEqual(reader.packet(replies[0], challenge=self.challenge, command=command)[1:],
                         (1, b'\x06'))
        self.assertEqual(self.connection.phase, 'primed')  # No claim of spawn yet.

    def test_challenge_identity_and_message_ack_are_bound_to_admission(self):
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.connection.receive(b'\xff'*4+b'getchallenge 0000000000000001\0')
        with self.assertRaisesRegex(ValueError, 'connected'):
            self.connection.receive(b'\xff'*4+b'stats\0\0\0\0')
        self.connect()
        for info in (self.info.replace(str(self.challenge),'0'),
                     self.info+r'\xuid\1234567812345678', self.info+';quit'):
            with self.assertRaises(ValueError):
                self.connection.receive(b'\xff'*4+f'connect {self.uid:016x} "{info}"\0'.encode())
        self.upload()
        for packet in (b'\0', self.packet(b'\x03', 1, ack=5),
                       self.packet(b'\x03', 1, server_id=100)):
            with self.assertRaises(ValueError):
                self.connection.receive(packet)
        self.assertTrue(self.connection.receive(self.packet(b'\x03', 1)))


if __name__ == '__main__':
    unittest.main()
