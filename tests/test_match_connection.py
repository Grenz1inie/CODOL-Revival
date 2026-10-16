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

    def test_current_client_fragments_complete_only_after_all_data(self):
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

    def test_match_upload_preserves_crc_from_before_native_profile_preparation(self):
        from match_server.connection import StatsTransfer
        # CDB at 0x6d81c4/0x6d81ca: 0x6d8a70 changes the body after CRC.
        # Match stats retain that word; they are not a lobby save envelope.
        profile = bytearray(profile_bytes())
        profile[3838] ^= 1
        for compressed in (False, True):
            source = zlib.compress(profile) if compressed else bytes(profile)
            transfer = StatsTransfer()
            for i in range((len(source)+1237)//1238):
                missing = transfer.accept(self.client.stats_fragment(source, i, compressed=compressed))
            self.assertEqual(missing, 0)
            self.assertEqual(transfer.profile, bytes(profile))

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

    def test_bad_zlib_or_size_never_publishes_a_profile(self):
        from match_server.connection import StatsTransfer
        valid = profile_bytes()
        damaged = bytearray(zlib.compress(valid))
        damaged[-1] ^= 1
        for source in (bytes(damaged), zlib.compress(valid)+b'tail',
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
        packet = self.packet(b'\x1a'+struct.pack('<I',1)+command+b'\0', 2,
                             ack=sequence, server_id=self.connection.server_id)
        replies = self.connection.receive(packet)
        self.assertEqual(reader.packet(replies[0], challenge=self.challenge, command=command)[1:],
                         (1, b'\x06'))
        self.assertEqual(self.connection.phase, 'primed')  # No claim of spawn yet.

    def test_initial_gamestate_keeps_native_frame_clock_at_normal_speed(self):
        from match_server.connection import Connection
        reader = ClientConnection423()
        for map_name in ('mp_nuked', 'mp_killhouse_sh'):
            connection = Connection(self.uid, netconst_checksum=55, map_name=map_name)
            reader.gamestate(connection.gamestate, checksum=55)
            for elapsed in (16, 50, 1000):
                with self.subTest(map=map_name, elapsed=elapsed):
                    self.assertEqual(reader.frame_milliseconds(elapsed), elapsed)

    def test_captured_first_netchan_uses_zero_server_id_until_gamestate(self):
        # Authenticated 2026-10-16 DATA; 0x4602a0 sends the unset map epoch as 0.
        self.connection.challenge = 535873589
        self.connect()
        self.upload()
        captured = bytes.fromhex('0100000000000000000000000036')
        replies = self.connection.receive(captured)
        self.assertEqual(self.connection.phase, 'primed')
        self.assertTrue(replies)
        self.assertEqual(self.connection.receive(captured), [])
        with self.assertRaisesRegex(ValueError, 'server id'):
            self.connection.receive(self.packet(b'\x03', 2, ack=1, server_id=0))
        self.assertTrue(self.connection.receive(self.packet(
            b'\x03', 2, ack=1, server_id=self.connection.server_id)))

    def test_map_category_and_current_serverinfo_maxclients(self):
        from unicorn.x86_const import UC_X86_REG_EBX, UC_X86_REG_EDI, UC_X86_REG_ESP
        wire=self.connection.gamestate
        self.assertEqual(wire[5:].split(b'\0',2)[:2],[b'mp_killhouse_sh',b'mp'])
        reader=ClientReader423()
        reader.gamestate(wire,checksum=0x11223344)
        cpu=reader.cpu
        offset,=struct.unpack('<I',cpu.mem_read(0x796f2dc,4))
        cpu.reg_write(UC_X86_REG_EDI,0x7976124+offset)
        cpu.reg_write(UC_X86_REG_EBX,0x30300000)
        cpu.reg_write(UC_X86_REG_ESP,0x303ff000)
        # Stock CG serverinfo consumer: Info_ValueForKey("2485") -> atoi -> maxclients.
        cpu.emu_start(0x579066,0x5790b9,count=20000)
        self.assertEqual(struct.unpack('<I',cpu.mem_read(0x30300064,4))[0],2)

    def test_db_loading_heartbeat_and_final_progress(self):
        self.connect()
        self.assertEqual(self.connection.receive(b'\xff'*4+b'heartbeat'),
                         [b'\xff'*4+b'heartbeatresponse'])
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        self.assertEqual(self.connection.receive(b'\xff'*4+b'gamestateupdate 6\0'),[])
        self.assertEqual(self.connection.loading_status,6)

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

    def test_current_quoted_challenge_reaches_connect_without_relaxing_identity(self):
        # Client 0x465d32 uses `getchallenge 0 "%s"`; confirmed by live DATA.
        request = b'\xff'*4+f'getchallenge 0 "{self.uid:016x}"\0'.encode()
        reply, = self.connection.receive(request)
        self.assertEqual(reply, b'\xff'*4+f'challengeResponse {self.connection.challenge}\0'.encode())
        self.assertEqual(self.connection.receive(request), [reply])
        self.assertEqual(self.connection.phase, 'reserved')
        for text in ('getchallenge 0 "0000000000000001"',
                     f'getchallenge 1 "{self.uid:016x}"',
                     f'getchallenge 0 "{self.uid:016x}',
                     f'getchallenge 0 "{self.uid:016x}" trailing'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.connection.receive(b'\xff'*4+text.encode())
        self.info = f'\\xuid\\{self.uid:016x}\\challenge\\{self.connection.challenge}\\name\\VGVzdA=='
        connected, = self.connection.receive(b'\xff'*4+f'connect {self.uid:016x} "{self.info}"\0'.encode())
        self.assertTrue(connected.startswith(b'\xff'*4+b'connectResponse '))
        self.assertEqual(self.connection.phase, 'connected')

    def test_batched_reliables_and_real_move_bits_do_not_shift_the_payload(self):
        from story_wire423 import _Message
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        message = _Message()
        command = f'userinfo "{self.info}"'.encode()
        for number in (1,2):
            message.bits(2,3)
            message.data.extend(struct.pack('<I',number)+command+b'\0')
        message.bits(3,3)
        self.connection.receive(self.packet(bytes(message.data),2,ack=1,server_id=self.connection.server_id))
        self.assertEqual(self.connection.reliable,2)
        key = 2 ^ self.connection.checksum_feed
        move = self.client.usercmd({'time':100,'buttons':1,'weapon':7,'forward':127},key=key,move=True)
        malformed = self.packet(move[:-1],3,ack=2,server_id=self.connection.server_id)
        with self.assertRaises(ValueError):
            self.connection.receive(malformed)
        self.assertEqual(self.connection.pending_commands,[])
        self.connection.receive(self.packet(move,3,ack=2,server_id=self.connection.server_id))
        self.assertEqual(len(self.connection.pending_commands),1)
        self.assertEqual(self.connection.pending_commands[0]['weapon'],7)
        self.assertEqual(self.connection.pending_commands[0]['buttons'],1)

    def test_score_and_action_notifications_preserve_bundled_move_and_reliable_ack(self):
        from match_server.input import usercmd_key
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        command = f'userinfo "{self.info}"'.encode()
        move = self.client.usercmd({'time':100,'buttons':1,'weapon':5,'forward':127},
            key=usercmd_key(1,self.connection.checksum_feed),move=True,
            reliables=((1,b's'),(2,command),(3,b'n 31'),(4,b'n 32'),
                       (5,b'n 1'),(6,b'n 2'),(7,b'n 98'),(8,b's')))
        packet = self.packet(move,2,ack=1,server_id=self.connection.server_id)
        replies = self.connection.receive(packet)
        self.assertEqual(self.connection.reliable,8)
        self.assertEqual(self.connection.command,b's')
        self.assertEqual(self.connection.pending_commands[0]['buttons'],1)
        self.assertEqual(self.connection.pending_commands[0]['weapon'],5)
        self.assertNotEqual(self.connection.pending_commands[0]['direction'],0)
        reader = ClientReader423()
        reader.reset_netchan()
        self.assertEqual(reader.packet(replies[0],challenge=self.challenge,command=b's')[1:],
                         (8,b'\x06'))
        self.assertEqual(self.connection.receive(packet),[])

    def test_score_poll_does_not_allow_reliable_gaps_or_unknown_commands(self):
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        for number,command in ((2,b's'),(1,b's extra'),(1,b'give all'),
                               (1,b'n 0'),(1,b'n 99'),(1,b'n 1;quit'),
                               (1,b'n -1'),(1,b'n 1 extra')):
            packet = self.packet(b'\x1a'+struct.pack('<I',number)+command+b'\0',2,
                                 ack=1,server_id=self.connection.server_id)
            with self.assertRaisesRegex(ValueError,'reliable client command'):
                self.connection.receive(packet)
            self.assertEqual((self.connection.received,self.connection.reliable),(1,0))
            self.assertEqual(self.connection.pending_commands,[])

    def test_weapon_command_and_acknowledged_snapshot_key_the_next_input(self):
        from match_server.input import usercmd_key
        from match_server.snapshot import encode_snapshot,Inventory
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        state={0:1000,39:7}
        reliable=self.connection.queue_command(b'a 7')
        self.connection.send(encode_snapshot(state,server_time=1000,health=100,
                                            inventory=Inventory(7,1,1,30,90)),player_fields=state)
        snapshot_sequence=self.connection.sent
        # The game carries weapon 7 from the acknowledged snapshot, omitting
        # its unchanged value from this usercmd's delta encoding.
        native_base={'time':0,'weapon':7}
        key=usercmd_key(snapshot_sequence,self.connection.checksum_feed,b'a 7')
        body=self.client.usercmd(native_base|{'time':1050,'buttons':1},key=key,base=native_base,move=True)
        encoded=bytearray(body)
        xor=(self.challenge ^ self.connection.server_id ^ snapshot_sequence)&255
        for i in range(len(encoded)):
            xor ^= (b'a 7'[i%3] << (i&1))&255
            encoded[i] ^= xor
        packet=struct.pack('<IBII',2,self.connection.server_id,snapshot_sequence,reliable)+encoded
        self.connection.receive(packet)
        self.assertEqual(self.connection.pending_commands[0]['weapon'],7)
        self.assertEqual(self.connection.pending_commands[0]['buttons'],1)
        self.assertEqual(self.connection.server_ack,reliable)

    def test_confirmed_snapshot_remains_input_base_while_client_lags(self):
        from match_server.input import usercmd_key
        from match_server.snapshot import encode_snapshot
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        state={0:1000,39:5}
        self.connection.send(encode_snapshot(state,server_time=1000,health=100),player_fields=state)
        acknowledged=self.connection.sent
        self.connection.receive(self.packet(b'\x03',2,ack=acknowledged),reply=False)
        # Rendering/background stalls can leave the client using its last
        # confirmed snapshot while the server publishes more than 64 frames.
        for time in range(1050,5050,50):
            newer=state|{0:time,39:7}
            self.connection.send(encode_snapshot(newer,server_time=time,health=100),player_fields=newer)
        base={'time':0,'weapon':5}
        body=self.client.usercmd(base|{'time':5050,'buttons':1,'forward':127},
            key=usercmd_key(acknowledged,self.connection.checksum_feed),base=base,move=True)
        packet=self.packet(body,3,ack=acknowledged)
        self.connection.receive(packet,reply=False)
        command,=self.connection.pending_commands
        self.assertEqual((command['weapon'],command['buttons'],command['direction']),(5,1,1))
        self.assertEqual(self.connection.receive(packet,reply=False),[])
        with self.assertRaisesRegex(ValueError,'unsent message'):
            self.connection.receive(self.packet(body,4,ack=self.connection.sent+1),reply=False)
        # Advancing to a new confirmed frame retires the old base normally.
        self.connection.receive(self.packet(b'\x03',4,ack=self.connection.sent),reply=False)
        self.connection.send(b'\x06')
        with self.assertRaisesRegex(ValueError,'expired input base'):
            self.connection.receive(self.packet(body,5,ack=acknowledged),reply=False)

    def test_loading_status_and_position_center_are_bound_to_the_map_state(self):
        from match_server.connection import Connection
        self.connection=Connection(self.uid,netconst_checksum=0x11223344,
                                   position_base=(3926,-925,8440))
        self.connect()
        self.upload()
        self.connection.receive(self.packet(b'\x03',1))
        for status in (2,3,3):
            self.assertEqual(self.connection.receive(b'\xff'*4+f'gamestateupdate {status}\0'.encode()),[])
        self.assertEqual(self.connection.loading_status,3)
        # No spawn claim from a loading notification alone.
        self.assertEqual(self.connection.phase,'primed')
        reader=ClientReader423()
        reader.gamestate(self.connection.gamestate,checksum=0x11223344)
        offset,=struct.unpack('<I',reader.cpu.mem_read(0x796f2dc+16*4,4))
        center=bytes(reader.cpu.mem_read(0x7976124+offset,64)).split(b'\0',1)[0]
        self.assertEqual(center,b'3926 -925 8440')
        with self.assertRaises(ValueError):
            self.connection.receive(b'\xff'*4+b'gamestateupdate 99\0')


if __name__ == '__main__':
    unittest.main()
