"""A standalone exported package is the only runtime resource dependency."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

def package(directory, map_name='mp_killhouse_sh', weapon_capacity=900):
    weapons=[f'fixture_{i}_mp' for i in range(351)]
    weapons[4]='acr_mp'
    header=bytearray(0xe28)
    for offset,value in ((0xd08,36),(0xd10,90),(0x71c,2000),(0x728,2500),(0x6dc,30),(0xbc8,22)):
        struct.pack_into('<I',header,offset,value)
    for offset,value in ((0xbcc,1500),(0xbe0,1501)):
        struct.pack_into('<f',header,offset,value)
    # An authored two-spawn floor; no old engine, profile or external asset path.
    geometry=dict(planes=[],sides=[],materials=[dict(contents=1)],
        brushes=[dict(mins=[-1000,-1000,-100],maxs=[1000,1000,0],first_side=0,
                      side_count=0,axial_materials=[0]*6,contents=1)],
        world_brushes=[0],vertices=[],triangles=[],partitions=[],world_partitions=[],
        static_models=[],closure=dict(blockers=[]))
    files={'baseline.bin':b'IWCB000\x01','weapon-acr.bin':bytes(header),
           'waypoints.csv':b'2\n0 0 0,1,stand\n200 0 0,0,stand\n'}
    objects={'geometry.json':geometry,'collision.json':{'physics_ready':True},
        'position.json':{'status':'server_selected','position_base':[0,0,0]},
        'spawns.json':[{'classname':'mp_dm_spawn','origin':[0,0,40],'angles':[0,0,0]},
                       {'classname':'mp_dm_spawn','origin':[200,0,40],'angles':[0,180,0]}],
        'ncs.json':{'registry':{'checksum':3852334052,'kinds':{'13':{'base':5443,'capacity':weapon_capacity,'reserved':1,'strings':weapons},
                                       '0':{'reserved':1,'strings':['body','hands']}}}},
        'loadout.json':{'weapon':{'name':'acr_mp','index':5,'header':'weapon-acr.bin'},
                        'body':{'name':'body','index':1},'hands':{'name':'hands','index':2}}}
    files.update({n:json.dumps(v).encode() for n,v in objects.items()})
    manifest=dict(schema_version=1,format_version=423,map=map_name,gametype='dm',
        physics_ready=True,baseline={'count':0},files={n:{'bytes':len(d),
            'sha256':hashlib.sha256(d).hexdigest()} for n,d in files.items()})
    directory.mkdir()
    for name,data in files.items():
        (directory/name).write_bytes(data)
    (directory/'manifest.json').write_text(json.dumps(manifest))


class MatchRuntimeTests(unittest.TestCase):
    def test_full_weapon_registry_is_rejected_before_publishing_a_recipe(self):
        from match_server.runtime import load_matchmaking
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path,weapon_capacity=352)
            with self.assertRaisesRegex(ValueError,'composed weapon slot'):
                load_matchmaking(path,port=0)

    def test_composed_acr_reaches_client_config_selection_and_separate_ammo_keys(self):
        from match_server.runtime import load_matchmaking
        from client_reader423 import ClientReader423
        from story_wire423 import encode_snapshot as baseline
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path,'mp_nuked')
            service=load_matchmaking(path,port=0)
            try:
                world=service.world
                self.assertEqual((world.weapon.index,world.weapon.ammo_type,world.weapon.clip_type),(352,5,352))
                service.find(1,bytes.fromhex('08010000000800000000080a000000079b1ff0d600'))
                client=ClientReader423()
                client.gamestate(service.server.connection.gamestate,checksum=3852334052)
                # Real configstring reader: append after stock slots, never replace ACR CS5448.
                offset,=struct.unpack('<I',client.cpu.mem_read(0x796f2dc+5795*4,4))
                self.assertNotEqual(offset,0)
                recipe=bytes(client.cpu.mem_read(0x7976124+offset,32)).split(b'\0',1)[0]
                self.assertEqual(recipe,b'** 5 0 0')
                self.assertEqual(bytes(client.cpu.mem_read(0x796f2dc+5448*4,4)),bytes(4))
                world.bot=False
                world.step([dict(time=1050,direction=0,buttons=1,yaw=0,pitch=0,
                                 weapon=352,offhand=0,alt=0)],milliseconds=50)
                client.snapshot(baseline({},server_time=0),sequence=0)
                snapshot=client.snapshot(world.snapshot()[0],sequence=1)
                player=snapshot['player_data']
                for offset,value in ((0x2a4,352),(0x340,352),(0x3dc,352),(0x3e0,35)):
                    self.assertEqual(struct.unpack_from('<I',player,offset)[0],value)
                self.assertEqual(struct.unpack_from('<I',snapshot['entities_data'][1],208)[0],352 | 352<<16)
                self.assertEqual(world.players[1].health,70)
            finally:
                service.close()

    def test_nuketown_package_drives_both_connection_and_client_map_identity(self):
        from match_server.runtime import load_matchmaking
        from client_reader423 import ClientReader423
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'nuketown'
            package(path,'mp_nuked')
            service=load_matchmaking(path,port=0)
            try:
                service.find(1,bytes.fromhex('08010000000800000000080a000000079b1ff0d600'))
                connection=service.server.connection
                challenge=connection.challenge
                request=f'connect 0000000000000001 "\\xuid\\0000000000000001\\challenge\\{challenge}"'
                reply,=connection.receive(b'\xff'*4+request.encode())
                self.assertIn(b'\\mapname\\mp_nuked\\gametype\\dm',reply)
                state=ClientReader423().gamestate(connection.gamestate,checksum=3852334052)
                self.assertEqual((state['map'],state['game_type']),('mp_nuked','dm'))
            finally:
                service.close()

    def test_package_registration_reaches_the_independent_udp_endpoint(self):
        from match_server.runtime import load_matchmaking
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path)
            service=load_matchmaking(path,port=0)
            try:
                query=bytes.fromhex('08010000000800000000080a000000079b1ff0d600')
                self.assertEqual(len(service.find(1,query)),1)
                self.assertEqual(service.server.map_state['netconst_checksum'],3852334052)
                self.assertEqual(len(service.world.players),2)
            finally:
                service.close()

    def test_standalone_package_creates_grounded_two_player_world(self):
        from match_server.runtime import load_world
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path)
            world=load_world(path)
            self.assertEqual([p.origin[2] for p in world.players],[0,0])
            self.assertEqual(world.weapon.clip_size,36)
            self.assertTrue(world.bot)
            self.assertEqual(world.body_model,1)
            self.assertEqual(world.hands_model,2)
            self.assertEqual(len(world.navigation.nodes),2)
            # Corrupted file and resource index drift must fail before publication.
            (path/'weapon-acr.bin').write_bytes(bytes(0xe28))
            with self.assertRaisesRegex(ValueError,'integrity'):
                load_world(path)

    def test_unready_map_is_not_published(self):
        from match_server.runtime import load_world
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'match'
            package(path)
            manifest=json.loads((path/'manifest.json').read_text())
            manifest['physics_ready']=False
            (path/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'collision'):
                load_world(path)


if __name__=='__main__':
    unittest.main()
