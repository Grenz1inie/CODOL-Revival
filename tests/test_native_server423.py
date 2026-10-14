"""The reused C server must emit messages accepted by the current x86 client."""
import ctypes
import _ctypes
from pathlib import Path
import sys
import struct
import tempfile
import unittest
import zlib
import subprocess
import json

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_native_server import STAGE, prepare, build_wire_probe, build_input_probe
from client_reader423 import ClientReader423
from story_netconst423 import LAYOUT


class NetConst(ctypes.Structure):
    _fields_ = [('name', ctypes.c_char_p), ('kind', ctypes.c_uint),
                ('source', ctypes.c_uint), ('count', ctypes.c_uint),
                ('values', ctypes.POINTER(ctypes.c_char_p))]


class NativeServer423Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory(dir=STAGE)
        cls.addClassCleanup(cls.directory.cleanup)
        source = prepare(Path(cls.directory.name) / 'source')
        library = Path(cls.directory.name) / 'wire.dll'
        build_wire_probe(source, library)
        cls.input_probe = Path(cls.directory.name) / 'input.exe'
        build_input_probe(source, cls.input_probe)
        cls.lib = ctypes.CDLL(str(library))
        cls.addClassCleanup(_ctypes.FreeLibrary, cls.lib._handle)
        cls.lib.native_configstrings.argtypes = [ctypes.c_void_p] + [ctypes.c_uint] * 6
        cls.lib.native_configstrings.restype = ctypes.c_size_t
        cls.lib.native_gamestate.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                            ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        cls.lib.native_gamestate.restype = ctypes.c_size_t
        cls.lib.native_playerstate.argtypes = [ctypes.c_void_p, ctypes.c_uint,
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint]
        cls.lib.native_playerstate.restype = ctypes.c_size_t
        cls.lib.native_registry.argtypes = [ctypes.POINTER(NetConst), ctypes.c_uint,
            ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p, ctypes.c_uint]
        cls.lib.native_registry.restype = ctypes.c_int
        cls.lib.native_usercmd.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint,
            ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint)]
        cls.lib.native_usercmd.restype = ctypes.c_int
        cls.lib.native_default_usercmd.argtypes = [ctypes.POINTER(ctypes.c_uint64),ctypes.POINTER(ctypes.c_uint)]
        cls.lib.native_snapshot.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
        cls.lib.native_snapshot.restype = ctypes.c_size_t
        cls.lib.native_inventory.argtypes = [ctypes.c_void_p] + [ctypes.c_uint]*5
        cls.lib.native_inventory.restype = ctypes.c_size_t
        cls.lib.native_packet.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p] + [ctypes.c_uint]*5
        cls.lib.native_packet.restype = ctypes.c_size_t
        cls.lib.native_resource_slots.argtypes = [ctypes.c_uint,ctypes.POINTER(ctypes.c_uint)]
        cls.lib.native_adapt_player.argtypes = [ctypes.c_void_p,ctypes.c_uint,
            ctypes.POINTER(ctypes.c_uint),ctypes.POINTER(ctypes.c_uint),ctypes.c_uint]
        cls.lib.native_adapt_player.restype = ctypes.c_size_t

    def setUp(self):
        self.buffer = ctypes.create_string_buffer(0x20000)
        self.client = ClientReader423()

    def registry(self, definitions, seed=0x12345678):
        tables = (NetConst * len(definitions))()
        for i, (name, kind, source, strings) in enumerate(definitions):
            values = (ctypes.c_char_p * len(strings))(*[s.encode() for s in strings])
            tables[i] = NetConst(name.encode(), kind, source, len(strings), values)
        summary = (ctypes.c_uint * 64)()
        self.buffer.raw = b'\0' * len(self.buffer)
        ok = self.lib.native_registry(tables, len(tables), seed, summary,
                                     self.buffer, len(self.buffer))
        return ok, list(summary), self.buffer.raw

    def test_native_registry_matches_current_layout_order_and_crc(self):
        ok, summary, names = self.registry([
            ('ncs_mdl_chi_alpha', 0, 0, ['a', 'c']),
            ('ncs_mdl_level', 0, 0, ['a', 'a', 'b']),
            ('ncs_mat_level', 1, 0, ['x']),
            ('ncs_fxt_level', 15, 0, ['ignored']),
            ('ncs_mdl_other', 0, 1, ['b', 'd']),
        ])
        self.assertEqual(ok, 1)
        for kind, (base, capacity, _) in enumerate(LAYOUT):
            self.assertEqual(summary[kind*3:kind*3+2], [base, capacity])
        self.assertTrue(names.startswith(b'a\0a\0b\0c\0d\0x\0'))
        self.assertEqual(summary[2], 5)
        self.assertEqual(summary[63], zlib.crc32(b'aabcxd', 0x12345678))

    def test_native_registry_respects_current_reserved_slots(self):
        for kind, limit in ((0, 1023), (8, 64), (13, 899), (17, 7), (18, 320)):
            with self.subTest(kind=kind):
                values = [str(i) for i in range(limit)]
                self.assertEqual(self.registry([('ncs_test_level', kind, 0, values)])[0], 1)
                self.assertEqual(self.registry([('ncs_test_level', kind, 0, values+['overflow'])])[0], 0)

    def test_native_decodes_commands_from_current_client(self):
        commands = [({'time': 5}, [5]+[0]*16),
                    ({'time': 20, 'buttons': 1, 'forward': 127, 'right': -127,
                      'pitch': 65535, 'yaw': 16384}, [20,1,65535,16384,0,9]+[0]*11),
                    ({'time': 1000, 'buttons': 0x220005, 'weapon': 1023,
                      'offhand': 2, 'alt': 3, 'roll': 32768, 'melee_yaw': 90.,
                      'melee_dist': 255, 'melee_target': 2047, 'location_x': 31,
                      'location_y': 128, 'location_angle': 255, 'remote_x': 9, 'remote_y': 200},
                     [1000,0x220005,0,0,32768,0,1023,2,3,16384,255,2047,31,128,255,9,200])]
        for key in (0, 1, 0xfedcba98):
            previous = (ctypes.c_uint * 17)()
            base = {}
            for command, expected in commands:
                with self.subTest(key=key, command=command):
                    wire = self.client.usercmd(command, key=key, base=base)
                    result = (ctypes.c_uint * 17)(*[0xdeadbeef]*17)
                    self.assertEqual(self.lib.native_usercmd(wire,len(wire),key,previous,result),1)
                    self.assertEqual(list(result),expected)
                    untouched = (ctypes.c_uint * 17)(*[0xdeadbeef]*17)
                    self.assertEqual(self.lib.native_usercmd(wire,len(wire)-1,key,previous,untouched),0)
                    self.assertEqual(list(untouched),[0xdeadbeef]*17)
                    previous, base = result, command

    def test_native_resources_resolve_static_dynamic_and_zero_based_slots(self):
        for kind,first in ((0,1),(13,1),(8,0),(14,0)):
            with self.subTest(kind=kind):
                result=(ctypes.c_uint*6)()
                self.assertEqual(self.lib.native_resource_slots(kind,result),1)
                self.assertEqual(list(result),[first,first+1,first+2]*2)

    def test_engine_state_reaches_current_motion_and_weapon_fields(self):
        word=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
        engine={0:1000,0x1c:word(12.5),0x20:word(-20),0x24:word(40),
                0x9c:word(20),0xa0:word(-10),0x14c:word(90),0x150:word(-180),
                0x10:0x1000,0xec:8,0x33c:17,0x340:18,0x328:19,0x348:word(1)}
        offsets=(ctypes.c_uint*len(engine))(*engine)
        values=(ctypes.c_uint*len(engine))(*engine.values())
        size=self.lib.native_adapt_player(self.buffer,len(self.buffer),offsets,values,len(engine))
        self.assertGreater(size,0)
        result,remaining=self.client.playerstate(self.buffer.raw[:size],server_time=0)
        self.assertEqual(remaining,b'\x06')
        actual={field[0]:value for field,value in zip(self.client.player_fields,result)}
        expected={0:1000,0x1c:word(12.5),0x20:word(-20),0x24:word(40),
                  0x14c:word(90),0x150:word(-180),
                  0x10:0x1000,0xf0:8,0x340:27,0x344:28,0x32c:29,0x34c:word(1)}
        self.assertEqual({key:actual[key] for key in expected},expected)
        for offset,value in ((0xa0,20),(0xa4,-10)):
            angle=struct.unpack('<f',struct.pack('<I',actual[offset]))[0]
            self.assertAlmostEqual(angle,value,delta=360/65536)

    def test_native_all_current_events_reach_client(self):
        slots=[i for i,f in enumerate(self.client.player_fields) if f[1]==-94]
        previous=(ctypes.c_uint64*235)()
        for start in range(0,len(self.client.event_widths),len(slots)):
            values=(ctypes.c_uint64*235)()
            for slot,event in zip(slots,range(start,min(start+len(slots),162))):
                width=self.client.event_widths[event]
                parameter=(1<<width)-1 if width else 0
                values[slot]=(parameter<<32)|event
            size=self.lib.native_playerstate(self.buffer,len(self.buffer),previous,values,0)
            self.assertGreater(size,0,f'events {start}..{start+len(slots)-1}')
            result,remaining=self.client.playerstate(self.buffer.raw[:size],server_time=0)
            self.assertEqual(result,list(values))
            self.assertEqual(remaining,b'\x06')

    def test_native_input_baseline_matches_current_client(self):
        word=lambda value:struct.unpack('<I',struct.pack('<f',value))[0]
        for fields in ({}, {39:17,40:18,53:19,19:word(90),18:word(-180),
                           70:word(20),45:word(-10),54:0x1000,28:8,41:word(1)},
                       {19:word(0.6*360/65536),54:0x1000,28:4,217:word(-1),20:0x4000}):
            with self.subTest(fields=fields):
                values=(ctypes.c_uint64*235)()
                for i,value in fields.items(): values[i]=value
                result=(ctypes.c_uint*17)()
                self.lib.native_default_usercmd(values,result)
                self.assertEqual(list(result),self.client.default_usercmd(fields))

    def test_native_initial_snapshot_reaches_current_baseline_store(self):
        size = self.lib.native_snapshot(self.buffer,len(self.buffer),1000)
        self.assertGreater(size,0)
        self.assertEqual(self.client.snapshot(self.buffer.raw[:size],sequence=1),
            {'server_time':1000,'sequence':1,'flags':8,'command_time':1000,
             'entities':0,'clients':0,'actors':0,'remaining':b'\x06'})

    def test_native_inventory_reaches_current_player_arrays(self):
        size = self.lib.native_inventory(self.buffer,len(self.buffer),1,511,2047,14)
        self.assertGreater(size,0)
        _, remaining = self.client.playerstate(self.buffer.raw[:size],server_time=0)
        self.assertEqual(remaining,b'\x06')
        read = lambda offset: struct.unpack('<I',self.client.cpu.mem_read(0x30290000+offset,4))[0]
        self.assertEqual(read(0x190),100)
        self.assertEqual(read(0x2a4),1)
        self.assertEqual(bytes(self.client.cpu.mem_read(0x302902e0,5)),b'\1'*5)
        self.assertEqual(read(0x3dc+14*12),1)
        self.assertEqual(read(0x3e0+14*12),511)
        self.assertEqual(read(0x364+14*8),1)
        self.assertEqual(read(0x368+14*8),2047)
        for weapon,clip,reserve,slot in ((1024,1,1,0),(1,512,1,0),(1,1,2048,0),(1,1,1,15)):
            with self.subTest(weapon=weapon,clip=clip,reserve=reserve,slot=slot):
                self.assertEqual(self.lib.native_inventory(self.buffer,len(self.buffer),
                    weapon,clip,reserve,slot),0)

    def test_native_fragmentation_reaches_current_netchan(self):
        for length in (1149,1150,2304,2305,0x20000-8):
            with self.subTest(length=length):
                payload=bytes(i%251 for i in range(length))
                packets=[]
                for index in range(128):
                    size=self.lib.native_packet(self.buffer,len(self.buffer),payload,len(payload),index,1,7,0x42)
                    if not size: break
                    packets.append(self.buffer.raw[:size])
                self.client.reset_netchan()
                if len(packets)>1:
                    self.assertEqual(struct.unpack_from('<H',packets[0],6)[0],0x482)
                result=None
                for packet in reversed(packets):
                    result=self.client.packet(packet,challenge=0x42,command=b'move%\xff')
                self.assertIsNotNone(result)
                self.assertEqual(result[:2],(1,7))
                self.assertTrue(result[2]==payload)
                self.assertIsNone(self.client.packet(packets[0],challenge=0x42,command=b'move%\xff'))

    def test_native_usermove_consumes_current_five_word_trailer(self):
        wire=self.client.usercmd({'time':1000,'buttons':1,'forward':127},key=123)
        wire+=struct.pack('<3fII',12.5,-20.,40.,975,0x12345678)
        fixture=Path(self.directory.name)/'input.bin'
        fixture.write_bytes(wire)
        result=json.loads(subprocess.check_output([str(self.input_probe),str(fixture),'123']))
        self.assertEqual(result,dict(ok=1,cursor=len(wire),time=975,origin=[12.5,-20.,40.]))
        fixture.write_bytes(wire[:-1])
        result=json.loads(subprocess.check_output([str(self.input_probe),str(fixture),'123']))
        self.assertEqual(result,dict(ok=0,cursor=0,time=0,origin=[0,0,0]))

    def test_native_aliases_and_recipes_reach_current_client(self):
        size = self.lib.native_configstrings(self.buffer, len(self.buffer), 0, 1, 127, 0, 1)
        self.assertGreater(size, 0)
        wire = self.buffer.raw[:size]
        self.assertEqual(wire[0], 4)
        rows, remaining = self.client.configstrings(wire[1:])
        self.assertEqual(rows, {0: 'current', 5444: '* 1', 5445: '** 1 127 0 1'})
        self.assertEqual(remaining, b'\x06')

    def test_native_current_recipe_limits_and_message_capacity(self):
        size = self.lib.native_configstrings(self.buffer, len(self.buffer), 7057, 1, 255, 511, 16383)
        self.assertGreater(size, 0)
        self.assertEqual(self.client.configstrings(self.buffer.raw[1:size]),
            ({7057: 'current', 5444: '* 1', 5445: '** 1 255 511 16383'}, b'\x06'))
        for index, aliases, camo, extra, attachment in (
                (7058,1,0,0,0), (0,1024,0,0,0), (0,1,256,0,0),
                (0,1,0,512,0), (0,1,0,0,16384)):
            with self.subTest(index=index, aliases=aliases, camo=camo, extra=extra):
                self.assertEqual(self.lib.native_configstrings(self.buffer, len(self.buffer),
                    index, aliases, camo, extra, attachment), 0)
        self.assertEqual(self.lib.native_configstrings(self.buffer, 4, 0, 1, 0, 0, 0), 0)

    def test_native_gamestate_uses_selected_category_and_current_bounds(self):
        size = self.lib.native_gamestate(self.buffer, len(self.buffer), b'mp_cargoship', b'coop', 0)
        self.assertGreater(size, 0)
        wire = self.buffer.raw[:size]
        self.assertTrue(wire.startswith(b'\x03\x07\0\0\0mp_cargoship\0coop\0'))
        result = self.client.gamestate(wire, checksum=0xc6280541)
        self.assertEqual(result['map'], 'mp_cargoship')
        self.assertEqual(result['game_type'], 'coop')
        self.assertEqual(result['client_number'], 0)
        for map_name, category, client in ((b'x'*32,b'coop',0), (b'mp_cargoship',b'bad',0),
                                            (b'mp_cargoship',b'coop',19)):
            with self.subTest(map=map_name, category=category, client=client):
                self.assertEqual(self.lib.native_gamestate(self.buffer, len(self.buffer),
                                                          map_name, category, client), 0)

    def test_native_player_writer_handles_current_field_order_and_protected_value(self):
        previous = (ctypes.c_uint64 * 235)()
        values = (ctypes.c_uint64 * 235)()
        requested = {0: 1000, 82: 63, 234: 1}
        for index, value in requested.items():
            values[index] = value
        size = self.lib.native_playerstate(self.buffer, len(self.buffer), previous, values, 1000)
        self.assertGreater(size, 0)
        result, remaining = self.client.playerstate(self.buffer.raw[:size], server_time=1000)
        self.assertEqual(result, list(values))
        self.assertEqual(remaining, b'\x06')

    def test_native_player_deltas_preserve_motion_angles_and_events(self):
        word = lambda f: struct.unpack('<I', struct.pack('<f', f))[0]
        previous = (ctypes.c_uint64 * 235)()
        values = (ctypes.c_uint64 * 235)()
        requested = {0: 1000, 1: 8, 3: 0xffff8000, 8: word(124.5),
                     10: word(-46.25), 11: word(333.75), 20: 0xfedcba98,
                     21: 36 | (31 << 32), 45: word(90.), 82: 12, 234: 1}
        for current in (requested, requested | {0: 1050, 1: 13, 8: word(125.5),
                                               45: word(-90.), 82: 0}):
            for i, value in current.items():
                values[i] = value
            size = self.lib.native_playerstate(self.buffer, len(self.buffer), previous, values, current[0])
            self.assertGreater(size, 0)
            result, remaining = self.client.playerstate(self.buffer.raw[:size], server_time=current[0],
                base={i: v for i,v in enumerate(previous) if v})
            self.assertEqual(result, list(values))
            self.assertEqual(remaining, b'\x06')
            previous = (ctypes.c_uint64 * 235)(*result)

    def test_native_packed_player_field_preserves_both_sections(self):
        previous = (ctypes.c_uint64 * 235)()
        for value in (0x1fff, 0x1f80, 0x7f, 0):
            values = (ctypes.c_uint64 * 235)(*previous)
            values[232] = value
            size = self.lib.native_playerstate(self.buffer, len(self.buffer), previous, values, 1000)
            self.assertGreater(size, 0)
            result, remaining = self.client.playerstate(self.buffer.raw[:size], server_time=1000,
                base={i: v for i,v in enumerate(previous) if v})
            self.assertEqual(result, list(values))
            self.assertEqual(remaining, b'\x06')
            previous = values
        values = (ctypes.c_uint64 * 235)(*previous)
        values[232] = 0x2000
        self.assertEqual(self.lib.native_playerstate(self.buffer, len(self.buffer),
                                                   previous, values, 1000), 0)


if __name__ == '__main__':
    unittest.main()
