"""Real loopback UDP with current DATA framing and native client consumers."""
import struct
import socket
import time
import unittest
import zlib

from client_connection423 import ClientConnection423
from client_reader423 import ClientReader423
from probe_native_connection import EncryptedPeer
from test_match_connection import profile_bytes


class MatchServerTests(unittest.TestCase):
    def test_nat_intro_reply_precedes_dtls_without_claiming_a_reservation(self):
        from match_server.server import MatchServer
        # bdNAT v2 INTRO: id, opaque client MAC, and two endpoints.
        intro=bytes.fromhex('0d020078563412001122334455667788997f00000131757f0000012a71')
        with MatchServer(1,b'12345678',bytes(16),netconst_checksum=55) as server:
            with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as peer:
                peer.settimeout(.3)
                endpoint=('127.0.0.1',server.port)
                for invalid in (intro[:-1],intro+b'x',intro[:1]+b'\x03'+intro[2:]):
                    peer.sendto(invalid,endpoint)
                    with self.assertRaises(socket.timeout):
                        peer.recvfrom(65535)
                peer.sendto(intro,endpoint)
                reply,address=peer.recvfrom(65535)
                self.assertEqual(address,endpoint)
                self.assertEqual(reply,bytes.fromhex('0c020078563412001122334455667788997f00000131757f0000012a71'))
                self.assertIsNone(server.association)
                peer.sendto(struct.pack('<BBHHH',1,2,0,0,123)+b'12345678',endpoint)
                ack,_=peer.recvfrom(65535)
                self.assertEqual(ack[:4],struct.pack('<BBH',2,2,123))
                self.assertEqual(len(ack),38)

    def test_current_client_input_changes_independent_world_over_encrypted_udp(self):
        from match_server.server import MatchServer
        from match_server.input import usercmd_key, FIELDS
        from test_match_world import MatchWorldTests
        world=MatchWorldTests().world()
        uid,sid,security=0x1234567812345678,b'12345678',bytes(range(16))
        events=[]
        with MatchServer(uid,sid,security,netconst_checksum=55,world=world,
                         record=lambda event,**fields:events.append((event,fields))) as server:
            client,reader=ClientConnection423(),ClientReader423()
            peer=EncryptedPeer(server.port,sid,security,client,current=True)
            try:
                challenge=int(peer.oob(f'getchallenge 0 "{uid:016x}"\0'.encode(),b'challengeResponse ').split()[1])
                info=f'\\xuid\\{uid:016x}\\challenge\\{challenge}\\name\\VGVzdA=='
                peer.oob(f'connect {uid:016x} "{info}"\0'.encode(),b'connectResponse ')
                profile=zlib.compress(profile_bytes())
                for i in range((len(profile)+1237)//1238):
                    peer.oob(b'stats\0'+client.stats_fragment(profile,i),b'statResponse ')
                peer.send(struct.pack('<IBII',1,255,0,0)+bytes([3^((challenge^255)&255)]))
                reader.reset_netchan()
                sequence,_,wire=reader.packet(peer.receive(),challenge=challenge)
                state=reader.gamestate(wire,checksum=55)
                self.assertEqual(server.connection.phase,'primed')
                outgoing,reliable,server_command=1,0,b''
                def send_move(values,base=None):
                    nonlocal outgoing
                    outgoing+=1
                    body=reader.usercmd(values,base=base,
                        key=usercmd_key(sequence,state['checksum_feed'],server_command),move=True)
                    server_id=server.connection.server_id
                    key=(challenge^server_id^sequence)&255
                    encoded=bytearray(body)
                    for i in range(len(encoded)):
                        if server_command:
                            key^=(server_command[i%len(server_command)] << (i&1))&255
                        encoded[i]^=key
                    peer.send(struct.pack('<IBII',outgoing,server_id,sequence,reliable)+encoded)
                def frame(minimum_time=0):
                    nonlocal sequence,reliable,server_command
                    deadline=time.monotonic()+3
                    while time.monotonic()<deadline:
                        decoded=reader.packet(peer.receive(),challenge=challenge)
                        if decoded is None:
                            continue
                        sequence,_,payload=decoded
                        cursor=0
                        while payload[cursor]==1:
                            number,=struct.unpack_from('<I',payload,cursor+1)
                            end=payload.index(0,cursor+5)
                            if number>reliable:
                                reliable,server_command=number,payload[cursor+5:end]
                            cursor=end+1
                        if payload[cursor]==0:
                            result=reader.snapshot(payload[cursor:],sequence=sequence)
                            if result['command_time']>=minimum_time and reader.snapshot_frame_ready(sequence):
                                return result
                    self.fail('no current-client snapshot')
                # Native client reaches state 9 and reports stages 1..6 before
                # sending any move: it needs its first playerstate to proceed.
                for stage in range(1,6):
                    peer.send(b'\xff'*4+f'gamestateupdate {stage}\0'.encode())
                peer.socket.settimeout(.2)
                with self.assertRaises(socket.timeout):
                    peer.receive()
                peer.socket.settimeout(3)
                peer.send(b'\xff'*4+b'gamestateupdate 6\0')
                initial_frame=frame()
                self.assertEqual((initial_frame['entities'],initial_frame['clients']),(2,2))
                self.assertEqual(server.connection.phase,'primed')
                self.assertIsNone(server.next_tick)  # No AI simulation before input.
                peer.send(b'\xff'*4+b'gamestateupdate 6\0')
                peer.socket.settimeout(.2)
                with self.assertRaises(socket.timeout):
                    peer.receive()
                peer.socket.settimeout(3)
                # The first post-gamestate move is admission, not proof of motion.
                send_move({'time':100})
                first=frame()
                self.assertEqual(server.connection.phase,'active')
                self.assertEqual((first['entities'],first['clients']),(2,2))
                self.assertEqual(server_command,b'a 5')
                initial=world.players[0].origin[:]
                target_time=first['server_time']+100
                base=dict(zip(FIELDS,reader.default_usercmd(world.snapshot()[1])))
                base.pop('direction')
                send_move({'time':target_time,'forward':127,'buttons':1,'weapon':5},
                          base=base)
                frame(target_time)
                self.assertGreater(world.players[0].origin[0],initial[0])
                self.assertEqual(world.players[0].clip,35)
                self.assertEqual(world.players[1].health,70)
                self.assertIsNone(server.last_error)
                self.assertTrue(any(k=='match_phase' and v['phase']=='active' for k,v in events))
                self.assertTrue(any(k=='match_state' and v['players'][1]['health']==70 for k,v in events))
            finally:
                peer.socket.close()

    def test_independent_udp_server_reaches_current_client_map_loading_context(self):
        from match_server.server import MatchServer
        uid, sid, security = 0x1234567812345678, b'12345678', bytes(range(16))
        with MatchServer(uid, sid, security, netconst_checksum=0x11223344) as server:
            client, reader = ClientConnection423(), ClientReader423()
            peer = EncryptedPeer(server.port, sid, security, client, current=True)
            try:
                challenge = int(peer.oob(f'getchallenge 0 "{uid:016x}"\0'.encode(),
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
