"""Independent state -> 3.3.3.3 client, with inventory and two player records."""
import struct
import unittest
from pathlib import Path
from client_reader423 import ClientReader423


def word(value):
    return struct.unpack('<I',struct.pack('<f',value))[0]


class MatchSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.client=ClientReader423()

    def pin_baseline(self):
        from story_wire423 import encode_snapshot as encode_baseline
        self.client.snapshot(encode_baseline({},server_time=0),sequence=0)

    def test_world_frames_pass_native_draw_gate_but_baseline_does_not(self):
        from reference_match.snapshot import encode_snapshot
        self.pin_baseline()
        self.assertFalse(self.client.snapshot_frame_ready(0))
        wire=encode_snapshot({0:1000},server_time=1000,health=100)
        self.client.snapshot(wire,sequence=1)
        self.assertTrue(self.client.snapshot_frame_ready(1))

    def test_nuketown_defers_fx_but_keeps_all_static_baseline_entities(self):
        from reference_match.snapshot import baseline_entities, encode_snapshot
        path=Path(__file__).resolve().parents[1]/'research/experiments/independent-match/nuketown-loadout-v2/baseline.bin'
        if not path.exists():
            self.skipTest('local current Nuketown fixture unavailable')
        data=path.read_bytes()
        entities=baseline_entities(data)
        self.assertEqual(len(entities),94)
        self.assertFalse({668,669,670,671}.intersection(n for n,_ in entities))
        wire=encode_snapshot({0:1000},server_time=1000,health=100,entities=entities)
        self.pin_baseline()
        result=self.client.snapshot(wire,sequence=1)
        self.assertEqual(result['entities'],94)
        unknown=bytearray(272)
        struct.pack_into('<II',unknown,0,900,14)  # A vehicle is not a deferred effect.
        with self.assertRaisesRegex(ValueError,'unsupported baseline'):
            baseline_entities(data+unknown)

    def test_health_weapon_ammo_and_two_players_reach_current_snapshot(self):
        from reference_match.snapshot import encode_snapshot, Inventory
        state={0:1000,8:word(100),10:word(25),11:word(-50),39:7,83:0}
        players=[(0,{24:word(100),28:word(-50),32:word(25)}),
                 (1,{24:word(200),28:word(80),32:word(25)})]
        clients=[(0,{20:5}),(1,{20:6})]
        wire=encode_snapshot(state,server_time=1000,health=100,
                             inventory=Inventory(7,1,1,30,90),entities=players,clients=clients)
        self.pin_baseline()
        result=self.client.snapshot(wire,sequence=1)
        self.assertEqual((result['entities'],result['clients'],result['command_time']),(2,2,1000))
        self.assertEqual(result['remaining'],b'\x06')
        data=result['player_data']
        self.assertEqual(struct.unpack_from('<3f',data,28),(100.,-50.,25.))
        for offset,value in ((0x190,100),(0x198,100),(0x340,7),(0x2a4,7),(0x3dc,1),(0x3e0,30),
                             (0x364,1),(0x368,90)):
            self.assertEqual(struct.unpack_from('<I',data,offset)[0],value,hex(offset))
        self.assertEqual([struct.unpack_from('<I',d,4)[0] for d in result['entities_data']],[1,1])
        self.assertEqual([struct.unpack_from('<I',d,20)[0] for d in result['clients_data']],[5,6])

    def test_player_entity_positions_and_angles_match_current_reader(self):
        from reference_match.snapshot import encode_player_entity
        wire=encode_player_entity({24:word(-1024),28:word(2048),32:word(37),64:word(90)})
        result,tail=self.client.entity(wire,base_type=0xffffffff)
        self.assertEqual(tail,b'\x06')
        for offset,value in ((24,-1024.),(28,2048.),(32,37.),(64,90.)):
            self.assertEqual(struct.unpack('<f',struct.pack('<I',result[offset]))[0],value)

    def test_authored_current_dm_baselines_are_visible_static_movers(self):
        from reference_match.snapshot import baseline_entities, encode_snapshot
        path=Path(__file__).resolve().parents[1]/'research/experiments/independent-match/killhouse-dm-v3/baseline.bin'
        if not path.exists():
            self.skipTest('local current baseline fixture unavailable')
        entities=baseline_entities(path.read_bytes())
        self.assertEqual(len(entities),156)
        wire=encode_snapshot({0:1000},server_time=1000,health=100,entities=entities)
        self.pin_baseline()
        result=self.client.snapshot(wire,sequence=1)
        self.assertEqual(result['entities'],156)
        for (_,expected),actual in zip(entities,result['entities_data']):
            self.assertEqual(struct.unpack_from('<I',actual,4)[0],6)
            for offset in (92,152,164,220):  # Registered model / brush model / sentinels.
                self.assertEqual(struct.unpack_from('<I',actual,offset)[0],expected.get(offset,0))
        with self.assertRaises(ValueError):
            baseline_entities(path.read_bytes()[:-1])

    def test_invalid_inventory_and_duplicate_players_are_rejected(self):
        from reference_match.snapshot import encode_snapshot, Inventory
        for inv in (Inventory(1024,1,1,1,1),Inventory(1,1,1,512,1),Inventory(1,1,1,1,2048)):
            with self.assertRaises(ValueError):
                encode_snapshot({},server_time=1000,health=100,inventory=inv)
        for rows in ([(1,{}),(0,{})],[(0,{}),(0,{})],[(2047,{})]):
            with self.assertRaises(ValueError):
                encode_snapshot({},server_time=1000,health=100,entities=rows)

    def test_view_angles_flags_and_fire_events_reach_current_player(self):
        from story_wire423 import encode_playerstate
        # 0x5a18e0 consumes the player's view angles; event pairs are uint64.
        values={0:1000,18:word(90),19:word(-45),28:0x1000,21:(17 << 32)|43}
        wire=encode_playerstate(values,server_time=1000)
        result,tail=self.client.playerstate(wire,server_time=1000)
        for index,value in values.items():
            self.assertEqual(result[index],value,index)
        self.assertEqual(tail,b'\x06')
        for values in ({21:162},{21:(1 << 40)|43},{18:0x7f800000},{28:1 << 30}):
            with self.assertRaises(ValueError):
                encode_playerstate(values,server_time=1000)

    def test_map_center_is_server_supplied_configstring_16(self):
        from story_wire423 import encode_gamestate
        from reference_match.snapshot import encode_player_entity
        from unicorn import UC_HOOK_CODE
        from unicorn.x86_const import UC_X86_REG_ESP,UC_X86_REG_EIP,UC_X86_REG_EAX
        captured=[]
        def scanf(cpu,address,size,context):
            # Replace only the CRT sscanf call. The shipped gamestate reader
            # still selects the configstring and all three destination globals.
            sp=cpu.reg_read(UC_X86_REG_ESP)
            text,fmt,*dest=struct.unpack('<5I',cpu.mem_read(sp,20))
            raw=bytes(cpu.mem_read(text,64)).split(b'\0',1)[0]
            format=bytes(cpu.mem_read(fmt,32)).split(b'\0',1)[0]
            captured.append((raw,format,dest))
            for pointer,value in zip(dest,map(float,raw.split())):
                cpu.mem_write(pointer,struct.pack('<f',value))
            cpu.reg_write(UC_X86_REG_EAX,3)
            cpu.reg_write(UC_X86_REG_EIP,0x46e0f1)
        hook=self.client.cpu.hook_add(UC_HOOK_CODE,scanf,begin=0x46e0ec,end=0x46e0ec)
        try:
            wire=encode_gamestate('mp_killhouse_sh','dm',55,command_sequence=0,client_number=0,
                 checksum_feed=0,ordinary=[(0,r'\mapname\mp_killhouse_sh\g_gametype\dm'),
                                          (16,'-1024.5 2000.5 17.5')])
            self.client.gamestate(wire,checksum=55)
        finally:
            self.client.cpu.hook_del(hook)
        self.assertEqual(captured,[(b'-1024.5 2000.5 17.5',b'%f %f %f',
                                    [0x78b0a78,0x78b0a7c,0x78b0a80])])
        origin={24:word(1000),28:word(2050),32:word(37)}
        wire=encode_player_entity(origin,position_base=(-1024,2001,18))
        values,_=self.client.entity(wire,base_type=0xffffffff)
        for offset,value in origin.items():
            self.assertEqual(values[offset],value)


if __name__ == '__main__':
    unittest.main()
