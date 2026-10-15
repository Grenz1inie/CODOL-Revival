"""Transport counter boundary used by the real loopback probe."""
import hmac
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from probe_native_connection import EncryptedPeer


class ProbeCounterTests(unittest.TestCase):
    def test_current_peer_records_match_native_data_writer(self):
        from client_connection423 import ClientConnection423
        from client_transport423 import ClientTransport423
        writer = ClientTransport423()
        peer = object.__new__(EncryptedPeer)
        peer.socket, peer.endpoint = Mock(), ('127.0.0.1', 1)
        peer.client, peer.current = ClientConnection423(), True
        peer.tag, peer.server_tag, peer.key = 713, 821, bytes(range(20))
        peer.sent, peer.received, peer.deferred = 65535, 65535, []
        plain = b'\xff'*4+b'stats\0'+bytes(range(256))*5
        peer.send(plain)
        self.assertEqual(peer.socket.sendto.call_args.args[0],
                         writer.data_packet(peer.key, peer.server_tag, 65536, plain))
        response = writer.data_packet(peer.key, peer.tag, 65536, b'response')
        peer.socket.recvfrom.return_value = response, peer.endpoint
        self.assertEqual(peer.receive(), b'response')
        with self.assertRaises(AssertionError):
            peer.receive()

    def test_receive_wrap_uses_full_counter_and_rejects_replay(self):
        peer = object.__new__(EncryptedPeer)
        peer.socket = Mock()
        peer.endpoint, peer.tag, peer.key = ('127.0.0.1', 1), 7, b'x'*24
        peer.received, peer.deferred = 65535, []
        peer.current = False
        peer.crypt = Mock(return_value=b'plain')
        header, data = struct.pack('<BBHH', 6, 2, 7, 0), b'encrypted'
        packet = header+hmac.digest(peer.key, header+data, 'sha1')[:8]+struct.pack('<H', len(data))+data
        peer.socket.recvfrom.return_value = packet, peer.endpoint
        self.assertEqual(peer.receive(), b'plain')
        peer.crypt.assert_called_once_with(data, 65536)
        with self.assertRaises(AssertionError):
            peer.receive()

    def test_send_wrap_keeps_full_crypto_counter(self):
        peer = object.__new__(EncryptedPeer)
        peer.socket, peer.endpoint = Mock(), ('127.0.0.1', 1)
        peer.sent, peer.server_tag, peer.key = 65535, 7, b'x'*24
        peer.current = False
        peer.crypt = Mock(return_value=b'encrypted')
        peer.send(b'plain')
        peer.crypt.assert_called_once_with(b'plain', 65536)
        self.assertEqual(peer.socket.sendto.call_args.args[0][:6], struct.pack('<BBHH', 6, 2, 7, 0))
