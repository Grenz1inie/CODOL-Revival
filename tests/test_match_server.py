"""Real loopback UDP; only the current client parser/hash runs in emulation."""
import struct
import unittest
import zlib

from client_connection423 import ClientConnection423
from client_reader423 import ClientReader423
from probe_native_connection import EncryptedPeer
from test_match_connection import profile_bytes


class MatchServerTests(unittest.TestCase):
    def test_independent_udp_server_reaches_current_client_map_loading_context(self):
        from match_server.server import MatchServer
        uid, sid, security = 0x1234567812345678, b'12345678', bytes(range(16))
        with MatchServer(uid, sid, security, netconst_checksum=0x11223344) as server:
            client, reader = ClientConnection423(), ClientReader423()
            peer = EncryptedPeer(server.port, sid, security, client)
            try:
                challenge = int(peer.oob(f'getchallenge {uid:016x}\0'.encode(),
                                         b'challengeResponse ').split()[1])
                info = f'\\xuid\\{uid:016x}\\challenge\\{challenge}\\name\\VGVzdA=='
                peer.oob(f'connect {uid:016x} "{info}"\0'.encode(), b'connectResponse ')
                source = zlib.compress(profile_bytes())
                for i in range((len(source)+1237)//1238):
                    result = peer.oob(b'stats\0'+client.stats_fragment(source,i), b'statResponse ')
                self.assertEqual(result, b'statResponse 0')
                peer.send(struct.pack('<IBII',1,255,0,0)+bytes([3^((challenge^255)&255)]))
                reader.reset_netchan()
                decoded = None
                while decoded is None:
                    decoded = reader.packet(peer.receive(), challenge=challenge)
                state = reader.gamestate(decoded[2], checksum=0x11223344)
                self.assertEqual((state['map'],state['game_type']),('mp_killhouse_sh','dm'))
                self.assertEqual(server.connection.phase,'primed')
                self.assertIsNone(server.last_error)
            finally:
                peer.socket.close()
        self.assertFalse(server.thread.is_alive())


if __name__ == '__main__':
    unittest.main()
