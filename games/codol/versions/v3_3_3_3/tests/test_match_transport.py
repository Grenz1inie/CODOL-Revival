"""Independent transport checked against the shipped client DATA serializer."""
import unittest
import struct
import hashlib

from cryptography.hazmat.primitives.asymmetric import ec

from client_connection423 import ClientConnection423
from client_transport423 import ClientTransport423


class MatchTransportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = ClientConnection423()
        cls.transport = ClientTransport423()

    def test_tiger_matches_current_client_at_padding_and_block_boundaries(self):
        from reference_match.crypto import tiger
        for length in (0, 3, 4, 44, 55, 56, 63, 64, 65, 128, 255):
            with self.subTest(length=length):
                data = bytes(range(length))
                self.assertEqual(tiger(data), self.client.tiger(data))
        self.assertEqual(tiger(b'abc').hex(), '2aab1484e8c158f2bfb8c5ff41b57a525129131c957b5f93')

    def test_handshake_and_encrypted_records_reach_a_current_client_peer(self):
        from reference_match.transport import Association
        sid, security = b'12345678', bytes(range(16))
        server = Association(sid, security, ('127.0.0.1', 42000))
        init = struct.pack('<BBHHH', 1, 2, 0, 0, 713)+sid
        ack = server.handshake(init)
        self.assertEqual(len(ack), 38)
        self.assertEqual(ack[:4], struct.pack('<BBH', 2, 2, 713))
        self.assertEqual(ack[24:], b'\x7f\0\0\x01'+struct.pack('<H', 42000)+sid)
        self.assertEqual(server.handshake(init), ack)
        private = ec.generate_private_key(ec.SECP224R1())
        point = private.public_key().public_numbers()
        def integer(value):
            raw = value.to_bytes(28, 'big')
            raw = (b'\0' if raw[0]&128 else b'')+raw
            return b'\x02'+bytes([len(raw)])+raw
        body = b'\x03\x02\x07\0\x02\x01\x1c'+integer(point.x)+integer(point.y)
        public = (b'\x30'+bytes([len(body)])+body).ljust(100, b'\0')
        tag, = struct.unpack_from('<H', ack, 16)
        echo = struct.pack('<BBHH', 3, 2, tag, 0)+ack+bytes(37)+sid+public
        cookie = server.handshake(echo)
        self.assertEqual(len(cookie), 114)
        self.assertEqual(cookie[:6], struct.pack('<BBHH', 4, 2, 713, 0))
        self.assertEqual(server.handshake(echo), cookie)
        p, xy = 15, []
        for _ in range(2):
            self.assertEqual(cookie[p], 2)
            n = cookie[p+1]
            xy.append(int.from_bytes(cookie[p+2:p+2+n], 'big'))
            p += n+2
        remote = ec.EllipticCurvePublicNumbers(*xy, ec.SECP224R1()).public_key()
        key = hashlib.sha1(private.exchange(ec.ECDH(), remote)+security).digest()
        def packet(value, counter):
            return self.transport.data_packet(key, tag, counter, value)
        # A fresh association may start above counter one; handle the wire rollover.
        for counter in (65534, 65535, 65536, 65537):
            value = b'\xff'*4+b'getchallenge '+str(counter).encode()
            encrypted = packet(value, counter)
            self.assertEqual(server.decrypt(encrypted), value)
            with self.assertRaises(ValueError):
                server.decrypt(encrypted)
        reply = server.encrypt(b'\xff'*4+b'challengeResponse 1234')
        self.assertEqual(reply[:4], struct.pack('<BBH', 6, 2, 713))
        self.assertEqual(reply, self.transport.data_packet(
            key, 713, 1, b'\xff'*4+b'challengeResponse 1234'))
        valid = packet(b'valid', 65538)
        for bad in (valid[:-1], valid[:6]+bytes(8)+valid[14:], valid[:2]+b'\0\0'+valid[4:]):
            with self.assertRaises(ValueError):
                server.decrypt(bad)
        self.assertEqual(server.decrypt(valid), b'valid')
        # A replayed INIT/COOKIE only resends its reply, never resets DATA counters.
        self.assertEqual(server.handshake(init), ack)
        self.assertEqual(server.handshake(echo), cookie)
        with self.assertRaises(ValueError):
            server.decrypt(valid)

    def test_invalid_handshake_never_opens_a_data_channel(self):
        from reference_match.transport import Association
        s = Association(b'12345678', bytes(16), ('127.0.0.1', 42000))
        for value in (b'', bytes(16), struct.pack('<BBHHH',1,2,0,0,1)+b'bad-sid!', bytes(189)):
            with self.subTest(value=value[:8]), self.assertRaises(ValueError):
                s.handshake(value)
        with self.assertRaises(ValueError):
            s.encrypt(b'not established')

    def test_invalid_cookie_does_not_open_a_data_channel(self):
        from reference_match.transport import Association
        s = Association(b'12345678', bytes(16), ('127.0.0.1', 42000))
        ack = s.handshake(struct.pack('<BBHHH',1,2,0,0,1)+b'12345678')
        echo = struct.pack('<BBHH',3,2,struct.unpack_from('<H',ack,16)[0],0)+ack+bytes(37)+b'12345678'+bytes(100)
        with self.assertRaisesRegex(ValueError, 'public key'):
            s.handshake(echo)
        with self.assertRaises(ValueError):
            s.encrypt(b'not established')


if __name__ == '__main__':
    unittest.main()
