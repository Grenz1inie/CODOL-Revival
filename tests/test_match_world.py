"""Authoritative behavior, using geometric queries rather than mocked hits."""
import math
import struct
import unittest

from match_server.collision import CollisionWorld


def room(*boxes):
    bounds = [((-1000,-1000,-100),(1000,1000,0)),*boxes]
    return CollisionWorld(dict(planes=[],sides=[],materials=[dict(contents=1)],
        brushes=[dict(mins=a,maxs=b,first_side=0,side_count=0,
                      axial_materials=[0]*6,contents=1) for a,b in bounds],
        world_brushes=list(range(len(bounds))),vertices=[],triangles=[],
        partitions=[],world_partitions=[],static_models=[],closure=dict(blockers=[])))


def command(time, *, direction=0, buttons=0, yaw=0, pitch=0):
    return dict(time=time,direction=direction,buttons=buttons,
                yaw=round(yaw*65536/360)&65535,pitch=round(pitch*65536/360)&65535,
                weapon=5,offhand=0,alt=0)


class MatchWorldTests(unittest.TestCase):
    def world(self, *, geometry=None, bot=False, second=(200,0,40)):
        from match_server.world import World, Weapon
        return World(geometry or room(),
                     [dict(origin=(0,0,40),angles=(0,0,0)),
                      dict(origin=second,angles=(0,180,0))],
                     Weapon(5,5,5,36,90,2000,2500,30,22,1500,1501),
                     body_model=104,hands_model=48,bot=bot)

    def test_grounded_movement_clips_wall_slides_and_rejects_time_replays(self):
        world=self.world(geometry=room(((100,-1000,0),(110,1000,200))))
        human=world.players[0]
        self.assertAlmostEqual(human.origin[2],0)
        for _ in range(30):
            world.step([command(world.time+50,direction=5)],milliseconds=50)
        self.assertLessEqual(human.origin[0],85.01)
        self.assertGreater(human.origin[0],80)
        self.assertLess(human.origin[1],-100)  # idTech right axis is -Y at yaw 0.
        self.assertAlmostEqual(human.origin[2],0,places=4)
        position=human.origin[:]
        world.step([command(human.command_time,direction=1),
                    command(world.time+10000,direction=1)],milliseconds=50)
        self.assertEqual(human.origin,position)

    def test_step_and_jump_use_swept_player_volume(self):
        world=self.world(geometry=room(((60,-100,0),(90,100,12))))
        human=world.players[0]
        heights=[]
        for _ in range(14):
            world.step([command(world.time+50,direction=1)],milliseconds=50)
            heights.append(human.origin[2])
        self.assertGreater(human.origin[0],100)
        self.assertGreaterEqual(max(heights),12)
        for _ in range(10):
            world.step([command(world.time+50)],milliseconds=50)
        before=human.origin[2]
        world.step([command(world.time+50,buttons=1024)],milliseconds=50)
        self.assertGreater(human.origin[2],before)
        for _ in range(30):
            world.step([command(world.time+50)],milliseconds=50)
        self.assertAlmostEqual(human.origin[2],0,places=3)

    def test_fire_rate_ammo_world_occlusion_death_and_authored_respawn(self):
        world=self.world()
        human,enemy=world.players
        for _ in range(7):
            world.step([command(world.time+50,buttons=1)],milliseconds=50)
        self.assertEqual((human.clip,enemy.health),(32,0))  # 90ms cooldown, 4 shots.
        self.assertEqual(human.kills,1)
        self.assertEqual(enemy.deaths,1)
        self.assertEqual(enemy.velocity,[0,0,0])
        deadline=enemy.respawn_at
        world.step(milliseconds=deadline-world.time-1)
        self.assertEqual(enemy.health,0)
        world.step(milliseconds=1)
        self.assertEqual(enemy.health,100)
        self.assertIn(tuple(enemy.origin),[(0,0,0),(200,0,0)])
        self.assertGreater(math.dist(human.origin,enemy.origin),30)

        blocked=self.world(geometry=room(((80,-100,0),(90,100,200))))
        for _ in range(10):
            blocked.step([command(blocked.time+50,buttons=1)],milliseconds=50)
        self.assertEqual(blocked.players[1].health,100)
        self.assertLess(blocked.players[0].clip,36)

    def test_reload_cannot_create_ammo_or_fire_before_completion(self):
        world=self.world()
        human=world.players[0]
        human.clip=1
        world.step([command(world.time+50,buttons=1)],milliseconds=50)
        world.step([command(world.time+50,buttons=16)],milliseconds=50)
        self.assertEqual(human.clip,0)
        self.assertEqual(human.reload_at,world.time+2500)
        reserve=human.reserve
        for _ in range(10):
            world.step([command(world.time+50,buttons=1)],milliseconds=50)
        self.assertEqual(human.clip,0)
        world.step(milliseconds=human.reload_at-world.time)
        self.assertEqual((human.clip,human.reserve),(36,reserve-36))
        human.clip=0
        human.reserve=3
        world.step([command(world.time+50,buttons=16)],milliseconds=50)
        world.step(milliseconds=2500)
        self.assertEqual((human.clip,human.reserve),(3,0))

    def test_ai_moves_aims_and_fires_through_the_same_weapon_rules(self):
        world=self.world(bot=True,second=(500,100,40))
        start=world.players[1].origin[:]
        for _ in range(70):
            world.step(milliseconds=50)
            if world.players[0].health == 0:
                break
        self.assertNotEqual(world.players[1].origin,start)
        self.assertLess(world.players[1].clip,36)
        self.assertEqual(world.players[0].health,0)
        self.assertEqual(world.players[1].kills,1)
        # A hidden target cannot be damaged by an AI health timer.
        blocked=self.world(geometry=room(((80,-1000,0),(90,1000,200))),bot=True)
        for _ in range(20):
            blocked.step(milliseconds=50)
        self.assertEqual(blocked.players[0].health,100)

    def test_current_client_reads_world_position_inventory_and_fire_event(self):
        from client_reader423 import ClientReader423
        from story_wire423 import encode_snapshot as encode_baseline
        world=self.world()
        world.step([command(1050,direction=1,buttons=1)],milliseconds=50)
        wire,fields=world.snapshot()
        client=ClientReader423()
        client.snapshot(encode_baseline({},server_time=0),sequence=0)
        result=client.snapshot(wire,sequence=1)
        data=result['player_data']
        self.assertEqual((result['entities'],result['clients']),(2,2))
        self.assertAlmostEqual(struct.unpack_from('<f',data,0x1c)[0],world.players[0].origin[0],places=3)
        self.assertEqual(struct.unpack_from('<I',data,0x190)[0],100)
        self.assertEqual(struct.unpack_from('<I',data,0x340)[0],5)
        self.assertEqual(struct.unpack_from('<I',data,0x3e0)[0],35)
        self.assertEqual(struct.unpack_from('<I',data,0x1f0)[0],2047)
        self.assertEqual(struct.unpack_from('<I',data,0xf8)[0],36)
        self.assertEqual(fields[0],1050)
        self.assertEqual(struct.unpack_from('<I',result['entities_data'][1],208)[0],5 | (5 << 16))

    def test_native_prediction_gets_full_size_standing_player(self):
        from client_reader423 import ClientReader423
        from story_wire423 import encode_snapshot as encode_baseline
        from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_ECX, UC_X86_REG_EDX, UC_X86_REG_ESP
        client=ClientReader423()
        client.snapshot(encode_baseline({},server_time=0),sequence=0)
        data=client.snapshot(self.world().snapshot()[0],sequence=1)['player_data']
        cpu=client.cpu
        state,bounds,stack,end=0x30200000,0x30210000,0x303ff000,0x303ffff0
        cpu.mem_write(state,bytes(data))
        cpu.mem_write(stack,struct.pack('<I',end))
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.reg_write(UC_X86_REG_EAX,state)
        # Native standing-height consumer: snapshot height alone is insufficient.
        cpu.emu_start(0x4124d0,end,count=10000)
        self.assertEqual(cpu.reg_read(UC_X86_REG_EAX),60)
        cpu.reg_write(UC_X86_REG_ESP,stack)
        cpu.reg_write(UC_X86_REG_EDX,state)
        cpu.reg_write(UC_X86_REG_ECX,bounds)
        cpu.emu_start(0x412560,end,count=10000)
        self.assertEqual(struct.unpack('<6f',cpu.mem_read(bounds,24)),(0,0,35,15,15,35))

    def test_spawn_counter_and_time_change_only_on_respawn_and_counter_wraps(self):
        from client_reader423 import ClientReader423
        from story_wire423 import encode_snapshot as encode_baseline
        world=self.world()
        player=world.players[0]
        client=ClientReader423()
        client.snapshot(encode_baseline({},server_time=0),sequence=0)
        sequence=0
        def spawn_state():
            nonlocal sequence
            sequence+=1
            data=client.snapshot(world.snapshot()[0],sequence=sequence)['player_data']
            return (struct.unpack_from('<I',data,0x19c)[0],struct.unpack_from('<I',data,0x3350)[0])
        self.assertEqual(spawn_state(),(1,1000))
        world.step([command(1050)],milliseconds=50)
        self.assertEqual(spawn_state(),(1,1000))
        for expected in (2,3):
            player.health=0
            player.respawn_at=world.time+3000
            world.step(milliseconds=2999)
            self.assertEqual(spawn_state()[0],expected-1)
            world.step(milliseconds=1)
            self.assertEqual(spawn_state(),(expected,world.time))
        player.spawn_count=255
        player.health=0
        player.respawn_at=world.time+3000
        world.step(milliseconds=3000)
        self.assertEqual(spawn_state(),(0,world.time))

    def test_current_death_mode_and_event_ring_survive_a_long_duel(self):
        from client_reader423 import ClientReader423
        from story_wire423 import encode_snapshot as encode_baseline
        world=self.world()
        player=world.players[0]
        player.health=0
        for _ in range(260):
            player.event(36)
        wire,fields=world.snapshot()
        self.assertEqual(fields[83],8)  # Current PM_DEAD; 7 is last stand.
        self.assertEqual(fields[1],4)
        client=ClientReader423()
        client.snapshot(encode_baseline({},server_time=0),sequence=0)
        state=client.snapshot(wire,sequence=1)['player_data']
        self.assertEqual(struct.unpack_from('<I',state,4)[0],8)
        self.assertTrue(struct.unpack_from('<I',state,0xf0)[0]&0x20000)


if __name__ == '__main__':
    unittest.main()
