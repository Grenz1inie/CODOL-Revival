"""Consume actual FF423 geometry without an engine or client executable."""
import sys
import unittest
import math
import struct
import json
import tempfile
from pathlib import Path
from functools import lru_cache
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'tools')]
import export_match_map as exporter

PACKAGE = ROOT / 'research/experiments/independent-match/killhouse-dm-v2'


@lru_cache(maxsize=1)
def actual_geometry():
    return exporter.read_geometry((PACKAGE / 'collision.bin').read_bytes(),
                                  (PACKAGE / 'gfxworld.bin').read_bytes())


class MatchCollisionTests(unittest.TestCase):
    def test_visibility_query_can_stop_at_any_obstacle_without_changing_nearest_hits(self):
        from match_server.collision import CollisionWorld
        from test_match_world import room
        # Far obstacle comes first in the exported order. Shooting and ground
        # queries still need the nearer obstacle; visibility needs only a hit.
        brushes=room(((120,-50,0),(130,50,100)),((60,-50,0),(70,50,100)))
        triangles=CollisionWorld(dict(materials=[dict(contents=1)],world_brushes=[],
            vertices=[[x,y,z] for x in (120,60) for y,z in ((-50,0),(50,0),(0,100))],
            triangles=[[0,1,2],[3,4,5]],partitions=[dict(first_tri=0,tri_count=2)],
            world_partitions=[[0,0]],static_models=[],closure=dict(blockers=[])))
        for world in (brushes,triangles):
            with self.subTest(world=world):
                start,end=[0,0,40],[200,0,40]
                self.assertAlmostEqual(world.trace_point(start,end,contents_mask=1)['fraction'],.3)
                self.assertTrue(world.trace_point(start,end,contents_mask=1,any_hit=True)['hit'])
                self.assertFalse(world.trace_point(start,[0,200,40],contents_mask=1,any_hit=True)['hit'])
                self.assertFalse(world.trace_point(start,end,contents_mask=2,any_hit=True)['hit'])
                self.assertAlmostEqual(world.trace_point(start,end,contents_mask=1)['fraction'],.3)

    def test_box_on_sloped_contact_cannot_round_through_the_surface(self):
        from match_server.collision import CollisionWorld
        # Reduced from the first Nuketown AI stall: the preceding sweep lands
        # on a slope, whose next contact time rounds a few ulps below zero.
        geometry = dict(materials=[dict(contents=1)],world_brushes=[],
            vertices=[[701,817.533203125,-64],[406.75,844,-62],
                      [1179.9996337890625,1084.26708984375,-64]],
            triangles=[[0,1,2]],partitions=[dict(first_tri=0,tri_count=1)],
            world_partitions=[[0,0]],static_models=[],closure=dict(blockers=[]))
        world = CollisionWorld(geometry)
        start = [801.3170703001568,879.5982372168976,-63.689413269572164]
        end = [798.3848270720862,878.8140310831764,-64.0]
        hit = world.trace_box(start,end)
        self.assertTrue(hit['hit'])
        self.assertFalse(hit['start_solid'])
        self.assertAlmostEqual(hit['fraction'],0)
        self.assertGreater(hit['normal'][2],.99)
        self.assertFalse(world.trace_box(hit['position'],hit['position'])['start_solid'])
        # Contact can still be left; this must not turn into an invisible wall.
        self.assertFalse(world.trace_box(start,[start[0],start[1],start[2]+1])['hit'])

    def test_nuketown_frozen_baseline_installs_dm_objects_and_retains_collision_masks(self):
        package = PACKAGE.parent / 'nuketown-dm-v2'
        if not (package/'geometry.json').is_file():
            self.skipTest('local Nuketown export unavailable')
        g = json.loads((package/'geometry.json').read_text())
        baseline = (package/'baseline.bin').read_bytes()
        report = exporter.classify_submodels((package/'entities.txt').read_bytes(), g)
        instances = exporter.select_dm_submodels(report, baseline, g)
        self.assertEqual(report['blockers'], [])
        self.assertEqual(len(instances), 32)
        self.assertTrue({15, 28, 65}.issubset({p['submodel'] for p in instances}))
        self.assertEqual(next(p for p in report['placements'] if p['submodel']==17)['activation'],
                         'baseline_has_no_collision_geometry')
        from match_server.collision import CollisionWorld
        ceiling = next(p for p in instances if p['submodel']==65)
        world = CollisionWorld(dict(g, world_brushes=[], world_partitions=[], static_models=[],
                                    submodel_instances=[ceiling]))
        self.assertEqual(g['submodels'][65]['brush_contents'], 0x08030200)
        hit = world.trace_point([-28, 814, 200], [-28, 814, 400], contents_mask=0x08030200)
        self.assertEqual(hit['submodel'], 65)
        self.assertFalse(world.trace_point([-28, 814, 200], [-28, 814, 400], contents_mask=1)['hit'])
        for offset, value, code in ((8, 1, 'I'), (12, 1, 'I'), (24, 999, 'f')):
            changed = bytearray(baseline)
            row = next(i for i in range(8,len(changed),272)
                       if struct.unpack_from('<I',changed,i+152)[0]==65)
            struct.pack_into('<'+code,changed,row+offset,value)
            current = exporter.classify_submodels((package/'entities.txt').read_bytes(),g)
            exporter.select_dm_submodels(current,bytes(changed),g)
            self.assertTrue(any('*65' in b for b in current['blockers']))

    def test_actual_frozen_export_is_ready_and_player_spawn_boxes_still_land(self):
        from match_server.mapdata import load_map
        from match_server.collision import CollisionWorld
        package = PACKAGE.parent/'killhouse-dm-v5'
        if not (package/'manifest.json').is_file():
            self.skipTest('local frozen-world export unavailable')
        data = load_map(package)
        self.assertTrue(data['manifest']['physics_ready'])
        self.assertEqual(data['manifest']['readiness_scope'],'dm_frozen_initial_static')
        self.assertEqual(data['submodel_placements']['installed_count'],78)
        self.assertEqual(data['geometry']['closure']['excluded_submodels'],38)
        self.assertEqual(data['files']['baseline.bin'],(PACKAGE/'baseline.bin').read_bytes())
        self.assertIsNone(data['ncs']['client_checksum'])
        self.assertFalse(data['ncs']['mounted_set_verified'])
        world = CollisionWorld(data['geometry'])
        world.require_ready()
        spawns = [s for s in data['spawns'] if s['classname']=='mp_dm_spawn']
        self.assertEqual(len(spawns),17)
        for spawn in spawns:
            x,y,z = spawn['origin']
            hit = world.trace_box([x,y,z],[x,y,z-512])
            self.assertEqual(hit['position'],[x,y,4])
            self.assertTrue(hit['complete'])
            self.assertFalse(hit['start_solid'])

    def test_ready_is_scoped_to_the_frozen_world_not_optional_dynamics(self):
        from match_server.collision import CollisionWorld
        g = dict(world_brushes=[],world_partitions=[],static_models=[],
                 closure=dict(frozen_world_ready=True,blockers=[],
                              excluded=['glass destruction','scripted moving objects','capsule parity']))
        w = CollisionWorld(g)
        w.require_ready()
        self.assertTrue(w.trace_point([0,0,0],[1,0,0],contents_mask=1)['complete'])
        self.assertTrue(w.trace_box([0,0,0],[1,0,0])['complete'])
        bad = CollisionWorld(dict(g,closure=dict(frozen_world_ready=False,blockers=['*11: baseline mismatch'])))
        with self.assertRaisesRegex(ValueError,r'\*11'):
            bad.require_ready()

    @unittest.skipUnless((PACKAGE/'baseline.bin').is_file(), 'local map export unavailable')
    def test_dm_placed_brush_and_gate_terrain_have_real_world_collision(self):
        from match_server.collision import CollisionWorld
        g = actual_geometry()
        report = exporter.classify_submodels((PACKAGE/'entities.txt').read_bytes(),g)
        instances = exporter.select_dm_submodels(report,(PACKAGE/'baseline.bin').read_bytes(),g)
        world = CollisionWorld(dict(g,world_brushes=[],world_partitions=[],static_models=[],
                                    submodel_instances=[p for p in instances if p['submodel']==11]))
        hit = world.trace_point([2990,-3944,25],[3100,-3944,25],contents_mask=0x2001001)
        self.assertEqual(hit['position'],[3032,-3944,25])
        self.assertEqual((hit['kind'],hit['entity_number'],hit['submodel']),('submodel_brush',456,11))
        self.assertEqual(world.trace_box([2990,-3944,25],[3100,-3944,25])['position'],[3017,-3944,25])
        self.assertFalse(world.trace_point([2990,-3944,25],[3100,-3944,25],contents_mask=1)['hit'])
        gate = CollisionWorld(dict(g,world_brushes=[],world_partitions=[],static_models=[],
                                   submodel_instances=[p for p in instances if p['submodel']==35]))
        # This gate component is a narrow diamond-section post, not a filled
        # doorway. Its oblique side at local x=.5 is y=-1, not AABB y=-1.5.
        hit = gate.trace_point([-854.5,-1200,32],[-854.5,-1180,32],contents_mask=1)
        self.assertEqual(hit['kind'],'submodel_triangle')
        self.assertAlmostEqual(hit['position'][1],-1192)
        box = gate.trace_box([-854.5,-1200,32],[-854.5,-1180,32],mins=(-.1,)*3,maxs=(.1,)*3)
        self.assertEqual(box['kind'],'submodel_triangle')
        self.assertAlmostEqual(box['position'][1],-1192.2)
        self.assertFalse(gate.trace_point([-853.6,-1192.4,32],[-853.6,-1191.4,32],contents_mask=1)['hit'])

    def test_rotated_submodel_keeps_oblique_brush_faces(self):
        from match_server.collision import CollisionWorld
        n = math.sqrt(.5)
        g = dict(planes=[[-n,0,n,0]],sides=[dict(plane=0,material=0)],materials=[dict(contents=1)],
            brushes=[dict(mins=[0,0,0],maxs=[2,2,2],first_side=0,side_count=1,
                          axial_materials=[0]*6,contents=1)],world_brushes=[],world_partitions=[],
            submodels=[{},dict(brushes=[0],partitions=[])],
            submodel_instances=[dict(submodel=1,entity_number=99,origin=[10,20,30],angles=[0,90,0])],
            closure=dict(blockers=[]))
        w = CollisionWorld(g)
        hit = w.trace_point([9,20.5,33],[9,20.5,29],contents_mask=1)
        self.assertAlmostEqual(hit['position'][2],30.5)
        self.assertAlmostEqual(hit['normal'][1],-n)
        self.assertAlmostEqual(hit['normal'][2],n)
        box = w.trace_box([9,20.5,33],[9,20.5,29],mins=(-.1,-.1,0),maxs=(.1,.1,.2))
        self.assertAlmostEqual(box['position'][2],30.6)
        self.assertFalse(w.trace_point([9,20.5,32.5],[9,20.5,31.5],contents_mask=1)['hit'])
        # A nearer world triangle replaces an earlier submodel hit completely.
        nearer = CollisionWorld(dict(g,vertices=[[8,20,31.5],[10,20,31.5],[8,22,31.5]],
                                     triangles=[[0,1,2]],partitions=[dict(first_tri=0,tri_count=1)],
                                     world_partitions=[[0,0]]))
        for query in (nearer.trace_point,nearer.trace_box):
            hit = query([9,20.5,33],[9,20.5,29],contents_mask=1) if query==nearer.trace_point else \
                query([9,20.5,33],[9,20.5,29],mins=(-.1,-.1,0),maxs=(.1,.1,.2),contents_mask=1)
            self.assertEqual(hit['kind'],'triangle')
            self.assertNotIn('entity_number',hit)
            self.assertNotIn('submodel',hit)

    @unittest.skipUnless((PACKAGE/'baseline.bin').is_file(), 'local map export unavailable')
    def test_dm_baseline_selects_exactly_the_78_authored_world_obstacles(self):
        g = actual_geometry()
        report = exporter.classify_submodels((PACKAGE/'entities.txt').read_bytes(),g)
        instances = exporter.select_dm_submodels(report,(PACKAGE/'baseline.bin').read_bytes(),g)
        self.assertEqual(len(instances),78)
        self.assertEqual(report['blockers'],[])
        self.assertEqual(sum(len(g['submodels'][i['submodel']]['brushes']) for i in instances),50)
        self.assertEqual({i['entity_number'] for i in instances if i['submodel']==11},{456})
        self.assertEqual(next(i for i in instances if i['submodel']==11)['origin'],[3051,-3944,25])
        self.assertTrue(all(i['angles']==[0,0,0] for i in instances))
        self.assertEqual(sum(len(g['submodels'][i['submodel']]['partitions']) for i in instances),93)
        self.assertEqual(sum(g['partitions'][p]['tri_count'] for i in instances
                             for p,_ in g['submodels'][i['submodel']]['partitions']),868)
        from match_server.collision import CollisionWorld,_cross,_sub,_dot
        for instance in instances:
            model = g['submodels'][instance['submodel']]
            if model['brushes']:
                brush = g['brushes'][model['brushes'][0]]
                center = [(a+b)/2 for a,b in zip(brush['mins'],brush['maxs'])]
                center[0] = brush['mins'][0]
                normal,mask = [-1,0,0],brush['contents']
            else:
                part,mat = model['partitions'][0]
                vertices = [g['vertices'][i] for i in g['triangles'][g['partitions'][part]['first_tri']]]
                center = [sum(v[i] for v in vertices)/3 for i in range(3)]
                normal = _cross(_sub(vertices[1],vertices[0]),_sub(vertices[2],vertices[0]))
                length = math.sqrt(_dot(normal,normal))
                normal,mask = [v/length for v in normal],g['materials'][mat]['contents']
            center = [a+b for a,b in zip(center,instance['origin'])]
            start,end = ([center[i]+sign*.01*normal[i] for i in range(3)] for sign in (1,-1))
            isolated = CollisionWorld(dict(g,world_brushes=[],world_partitions=[],static_models=[],submodel_instances=[instance]))
            with self.subTest(submodel=instance['submodel']):
                self.assertEqual(isolated.trace_point(start,end,contents_mask=mask)['entity_number'],instance['entity_number'])
                self.assertEqual(isolated.trace_box(start,end,mins=(-.0001,)*3,maxs=(.0001,)*3,
                                                    contents_mask=mask)['entity_number'],instance['entity_number'])
        # Presence in a baseline is not by itself activation in this frozen mode.
        excluded = next(p for p in report['placements'] if p['submodel']==2)
        self.assertTrue(excluded['baseline_present'])
        self.assertFalse(excluded['installed'])
        self.assertEqual(excluded['category'],'gametype_object')
        # A pose mismatch must remain explicit, not silently use an authored guess.
        damaged = bytearray((PACKAGE/'baseline.bin').read_bytes())
        for offset in range(8,len(damaged),272):
            if struct.unpack_from('<I',damaged,offset+0x98)[0] == 11:
                struct.pack_into('<f',damaged,offset+0x18,999)
        report = exporter.classify_submodels((PACKAGE/'entities.txt').read_bytes(),g)
        instances = exporter.select_dm_submodels(report,bytes(damaged),g)
        self.assertEqual(len(instances),77)
        self.assertTrue(any('*11' in message for message in report['blockers']))

    @unittest.skipUnless((PACKAGE/'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_spatial_candidates_preserve_actual_map_results_and_reduce_work(self):
        from match_server.collision import CollisionWorld
        world = CollisionWorld(actual_geometry())
        # An exhaustive candidate provider is the old scan path: compare
        # public query results, including ties, normals and start_solid flags.
        exhaustive = (list(range(len(world.brushes))),list(range(len(world.triangles))),
                      list(range(len(world.geometry['static_models']))))
        samples = [([3024,-826,48],[3024,-826,-20]),
                   ([3024,-826,4],[3200,-826,4]),
                   ([-1264.5,-3410,9],[-1264.5,-3406,9]),
                   ([0,0,500],[500,500,-50])]
        for start,end in samples:
            for method in (world.trace_point,world.trace_box):
                indexed = method(start,end,contents_mask=0x2001001)
                with patch.object(world,'_candidates',return_value=exhaustive):
                    brute = method(start,end,contents_mask=0x2001001)
                self.assertEqual(indexed,brute)
        candidates = world._candidates([3009,-841,-20],[3039,-811,118])
        self.assertLess(sum(map(len,candidates)),sum(map(len,exhaustive))//20)

    def test_repeated_triangle_box_queries_reuse_sat_projections(self):
        import match_server.collision as collision
        geometry = dict(materials=[dict(contents=1)],world_brushes=[],
            vertices=[[0,0,0],[4,0,0],[0,4,0]],triangles=[[0,1,2]],
            partitions=[dict(first_tri=0,tri_count=1)],world_partitions=[[0,0]],
            static_models=[],closure=dict(blockers=[]))
        world = collision.CollisionWorld(geometry)
        with patch.object(collision,'_projections',wraps=collision._projections) as projections:
            first = world.trace_box([1,1,4],[1,1,-4],mins=(-.1,-.1,0),maxs=(.1,.1,.2))
            count = projections.call_count
            self.assertEqual(first['kind'],'triangle')
            self.assertEqual(count,1)
            second = world.trace_box([1,1,4],[1,1,-4],mins=(-.1,-.1,0),maxs=(.1,.1,.2))
            self.assertEqual(first,second)
            self.assertEqual(projections.call_count,count)

    def test_long_diagonal_only_expands_geometry_on_the_swept_segment(self):
        import match_server.collision as collision
        vertices=[]
        for x,y in [(20+i,300+i) for i in range(40)]+[(249,249)]:
            vertices.extend(((x,y,0),(x+3,y,0),(x,y+3,0)))
        geometry=dict(materials=[dict(contents=1)],world_brushes=[],vertices=vertices,
            triangles=[[i,i+1,i+2] for i in range(0,len(vertices),3)],
            partitions=[dict(first_tri=0,tri_count=41)],world_partitions=[[0,0]],
            static_models=[],closure=dict(blockers=[]))
        world=collision.CollisionWorld(geometry)
        with patch.object(collision,'_projections',wraps=collision._projections) as projections:
            hit=world.trace_box([0,0,1],[500,500,-1],mins=(-.1,)*3,maxs=(.1,)*3)
            self.assertTrue(hit['hit'])
            self.assertEqual(hit['index'],40)
            self.assertEqual(projections.call_count,1)
        hit=world.trace_point([0,0,1],[500,500,-1],contents_mask=1)
        self.assertEqual(hit['index'],40)
        self.assertAlmostEqual(hit['fraction'],.5)
        # Stationary overlap and exact tangency remain candidates too.
        self.assertTrue(world.trace_box([250,250,0],[250,250,0],mins=(-.1,)*3,maxs=(.1,)*3)['start_solid'])
        self.assertFalse(world.trace_box([250,250,.1],[251,251,.1],mins=(-.1,)*3,maxs=(.1,)*3)['hit'])

    @unittest.skipUnless((PACKAGE / 'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_first_static_model_is_recovered_from_existing_gfxworld(self):
        from match_xmodel423 import read_static_models
        g = actual_geometry()
        models = read_static_models((PACKAGE/'gfxworld.bin').read_bytes(),
                                    g['provenance']['plane_offset'],g['provenance']['plane_reference'])
        model = models[0x3259a729]
        self.assertTrue(model['name'])
        self.assertTrue(model['surfaces'])
        self.assertTrue(any(s['records'] for s in model['surfaces']))
        self.assertEqual(model['name'], 'com_water_tank2')
        self.assertEqual(len(model['surfaces'][0]['triangles']), 142)
        # Independent expected surface height comes from the serialized plane,
        # not its AABB (top is 279.93147). The true water-tank lid is lower.
        from match_server.collision import CollisionWorld
        instance = dict(g['static_models'][0],geometry=str(0x3259a729))
        world = CollisionWorld(dict(g,world_brushes=[],world_partitions=[],
                                    static_models=[instance],xmodels={str(0x3259a729):model}))
        triangle = model['surfaces'][0]['triangles'][0]
        local = [sum(v[i] for v in triangle)/3 for i in range(3)]
        # The first real placement is essentially identity, including a tiny
        # serialized z rotation; choose a point well inside the lid triangle.
        x,y = instance['origin'][0]+local[0],instance['origin'][1]+local[1]
        z = instance['origin'][2]+model['surfaces'][0]['records'][0][3]
        hit = world.trace_point([x,y,z+3],[x,y,z-3],contents_mask=1)
        self.assertEqual(hit['kind'], 'static_model')
        self.assertAlmostEqual(hit['position'][2], z, places=5)
        self.assertEqual(hit['unresolved_static_models'], [])
        box = world.trace_box([x,y,z+3],[x,y,z-3],mins=(-.1,-.1,0),maxs=(.1,.1,.2),contents_mask=1)
        self.assertEqual(box['kind'], 'static_model')
        self.assertAlmostEqual(box['position'][2], z, places=5)
        self.assertFalse(world.trace_point([x,y,z+3],[x,y,z-3],contents_mask=2)['hit'])
        # Compare both BVH levels against exhaustive candidates on a real model.
        rows,spatial = world._static_cache[0]
        with patch.object(world,'_candidates',return_value=([],[],[0])), \
             patch.object(spatial,'query',return_value=list(range(len(rows)))):
            self.assertEqual(world.trace_point([x,y,z+3],[x,y,z-3],contents_mask=1),hit)
            import match_server.collision as collision
            with patch.object(collision,'_projections',wraps=collision._projections) as projections:
                repeated = world.trace_box([x,y,z+3],[x,y,z-3],mins=(-.1,-.1,0),maxs=(.1,.1,.2),contents_mask=1)
                self.assertEqual(repeated,box)
                self.assertEqual(projections.call_count,0)

    @unittest.skipUnless((PACKAGE/'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_all_static_references_resolve_with_current_common_mp(self):
        from match_xmodel423 import install_static_models
        zone_path = ROOT/'research/experiments/story-native/zone-assets/common_mp/zone.bin'
        if not zone_path.is_file():
            self.skipTest('current decoded common_mp unavailable')
        g = dict(actual_geometry(),static_models=[dict(m) for m in actual_geometry()['static_models']])
        report = install_static_models(g,(PACKAGE/'gfxworld.bin').read_bytes(),
                                      {'common_mp':zone_path.read_bytes()})
        self.assertEqual(report['resolved'],120)
        self.assertEqual(report['unresolved'],[])
        self.assertEqual(report['triangle_records'],45741)
        self.assertEqual(len(g['xmodels']),120)
        self.assertTrue(all(m['geometry'] is not None for m in g['static_models']))
        external = next(m for m in g['xmodels'].values() if m['name'] == 'com_plasticcase_beige_big')
        self.assertEqual(external['provenance']['zone_sha256'],
                         '76c3d9de35005b25f29e64593b65a524b0661646f9114c9dd1ed1cafa07ad60c')
        self.assertEqual(len(external['surfaces'][0]['triangles']),984)
        # Comma-prefixed placeholders are unresolved without their definition,
        # never silently accepted as empty/non-colliding models.
        missing = dict(actual_geometry(),static_models=[dict(m) for m in actual_geometry()['static_models']])
        closure = install_static_models(missing,(PACKAGE/'gfxworld.bin').read_bytes())
        self.assertEqual(closure['resolved'],116)
        self.assertEqual(len(closure['unresolved']),4)
        self.assertTrue(any(m['geometry'] is None for m in missing['static_models']))
        # Every reconstructed vertex must satisfy the actual 423 covectors.
        for model in g['xmodels'].values():
            for surface in model['surfaces']:
                for record,triangle in zip(surface['records'],surface['triangles']):
                    for vertex,(u,v) in zip(triangle,((0,0),(1,0),(0,1))):
                        dot = lambda a: sum(x*y for x,y in zip(a,vertex))
                        self.assertAlmostEqual(dot(record[:3]),record[3],places=5)
                        self.assertAlmostEqual(dot(record[4:7])-record[7],u,places=5)
                        self.assertAlmostEqual(dot(record[8:11])-record[11],v,places=5)
                        self.assertTrue(all(surface['mins'][i]-1e-5 <= vertex[i] <= surface['maxs'][i]+1e-5
                                            for i in range(3)))
        # Exercise one actual placement for EVERY resolved reference, including
        # rotated/scaled and multi-bone models, through both public consumers.
        from match_server.collision import CollisionWorld,model_to_world,_cross,_sub,_dot
        for key,model in g['xmodels'].items():
            instance = next(m for m in g['static_models'] if m['geometry'] == key)
            surface = next(s for s in model['surfaces'] if s['triangles'] and s['contents'])
            vertices = [model_to_world(v,instance) for v in surface['triangles'][0]]
            center = [sum(v[i] for v in vertices)/3 for i in range(3)]
            n = _cross(_sub(vertices[1],vertices[0]),_sub(vertices[2],vertices[0]))
            length = math.sqrt(_dot(n,n))
            start = [center[i]+n[i]/length*.01 for i in range(3)]
            end = [center[i]-n[i]/length*.01 for i in range(3)]
            world = CollisionWorld(dict(g,world_brushes=[],world_partitions=[],static_models=[instance]))
            with self.subTest(model=model['name'],reference=key):
                self.assertEqual(world.trace_point(start,end,contents_mask=surface['contents'])['kind'],'static_model')
                self.assertEqual(world.trace_box(start,end,mins=(-.0001,)*3,maxs=(.0001,)*3,
                                                 contents_mask=surface['contents'])['kind'],'static_model')

    def test_static_triangle_transform_rotation_scale_and_not_bounds(self):
        from match_server.collision import CollisionWorld
        geometry = dict(materials=[],world_brushes=[],world_partitions=[],closure=dict(blockers=[]),
            static_models=[dict(model_reference=123,geometry='123',origin=[10,20,30],
                                inverse_scaled_axis=[0,.5,0,-.5,0,0,0,0,.5],
                                mins=[10,16,30],maxs=[14,20,30])],
            xmodels={'123':dict(surfaces=[dict(contents=1,surface_flags=7,triangles=[[[0,0,0],[2,0,0],[0,2,0]]])])})
        world = CollisionWorld(geometry)
        hit = world.trace_point([11,19,32],[11,19,28],contents_mask=1)
        self.assertEqual(hit['position'],[11,19,30])
        self.assertEqual(hit['kind'],'static_model')
        self.assertEqual(hit['surface_flags'],7)
        box = world.trace_box([11,19,32],[11,19,28],mins=(-.1,-.1,0),maxs=(.1,.1,.2))
        self.assertAlmostEqual(box['position'][2],30)
        # Both are inside the placement AABB, but outside the real triangle.
        self.assertFalse(world.trace_point([13.8,16.2,32],[13.8,16.2,28],contents_mask=1)['hit'])
        self.assertFalse(world.trace_box([13.8,16.2,32],[13.8,16.2,28],
                                       mins=(-.1,-.1,0),maxs=(.1,.1,.2))['hit'])

    @unittest.skipUnless((PACKAGE / 'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_existing_package_gets_hashed_geometry_grounding_and_selected_center(self):
        from match_server.mapdata import load_map
        with tempfile.TemporaryDirectory(dir=PACKAGE.parent) as folder:
            output = Path(folder) / 'map'
            report = exporter.export_geometry_package(PACKAGE, output)
            loaded = load_map(output)
            self.assertIsNotNone(loaded['geometry'])
            self.assertEqual(loaded['files']['baseline.bin'], (PACKAGE/'baseline.bin').read_bytes())
            self.assertEqual(loaded['files']['ncs.json'], (PACKAGE/'ncs.json').read_bytes())
            position = loaded['position']
            self.assertTrue(position['server_selected'])
            self.assertTrue(position['client423_verified'])
            self.assertFalse(position['authored_center'])
            self.assertEqual(position['configstring_index'], 16)
            self.assertEqual(position['position_base'], [1859,-80,2083])
            for axis in range(3):
                lo,hi = position['quantized_bounds']['mins'][axis],position['quantized_bounds']['maxs'][axis]
                base = position['position_base'][axis]
                self.assertGreaterEqual(lo,base-32768)
                self.assertLessEqual(hi,base+32767)
            ground = loaded['spawn_grounding']
            self.assertEqual(len(ground['points']),372)
            point = next(p for p in ground['points'] if p['entity_index'] == 79)
            self.assertEqual(point['trace']['position'], [3024,-826,4])
            self.assertFalse(point['trace']['safe_spawn'])
            self.assertFalse(report['physics_ready'])
            self.assertIn('geometry.json',report['files'])
            self.assertEqual(loaded['static_model_closure']['resolved'],116)
            placements = json.loads(loaded['files']['submodel-placements.json'])
            self.assertEqual(placements['counts'],dict(placed_world_obstacle=78,gametype_object=20,
                                                       scripted_training_object=15,dynamic_utility=3))
            self.assertEqual(placements['unreferenced'],[])
            with self.assertRaisesRegex(ValueError,'current423 package input'):
                exporter.export_geometry_package(PACKAGE,Path(folder)/'wrong-version',
                                                 model_zones={'common_mp':b'unverified zone'})
            # The loader verifies new geometry just like original payloads.
            (output/'geometry.json').write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'integrity'):
                load_map(output)

    def test_point_trace_clips_oblique_planes_and_triangle_interior(self):
        from match_server.collision import CollisionWorld
        n = math.sqrt(.5)
        geometry = dict(physics_ready=False, planes=[[-n,0,n,0]], sides=[dict(plane=0,material=0)],
            materials=[dict(contents=1)],
            brushes=[dict(mins=[0,0,0],maxs=[2,2,2],first_side=0,side_count=1,
                          axial_materials=[0]*6,contents=1)],world_brushes=[0],
            vertices=[[4,0,0],[6,0,0],[4,2,2]],triangles=[[0,1,2]],
            partitions=[dict(first_tri=0,tri_count=1)],world_partitions=[[0,0]],
            closure=dict(blockers=['static model closure unknown']))
        geometry['static_models'] = [dict(mins=[5,1,-1],maxs=[6,2,4],model_reference=0x30000101,geometry=None)]
        world = CollisionWorld(geometry)
        hit = world.trace_point([.5,1,3],[.5,1,-1],contents_mask=1)
        self.assertAlmostEqual(hit['position'][2], .5)
        self.assertEqual(hit['kind'], 'brush')
        self.assertFalse(hit['complete'])
        self.assertAlmostEqual(hit['normal'][2], n)
        hit = world.trace_point([4.5,.5,3],[4.5,.5,-1],contents_mask=1)
        self.assertAlmostEqual(hit['position'][2], .5)
        self.assertEqual(hit['kind'], 'triangle')
        missing = world.trace_point([5.8,1.8,3],[5.8,1.8,-1],contents_mask=1)
        self.assertFalse(missing['hit'])  # Missing static AABB must NOT become collision.
        self.assertEqual(missing['unresolved_static_models'], [0])
        self.assertFalse(missing['complete'])
        self.assertFalse(world.trace_point([.5,1,3],[.5,1,-1],contents_mask=2)['hit'])
        self.assertTrue(world.trace_point([1,1,.5],[1,1,3],contents_mask=1)['start_solid'])
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            world.require_ready()
        self.assertEqual(world.ground_point([.5,1,.5])['position'], [.5,1,.5])

        # The moving box is allowed; the stationary brush remains a wedge.
        box = world.trace_box([.5,1,3],[.5,1,-1],mins=(-.1,-.1,0),maxs=(.1,.1,.4),contents_mask=1)
        self.assertAlmostEqual(box['position'][2], .6)
        self.assertEqual(box['kind'], 'brush')
        self.assertFalse(box['start_solid'])
        # Swept triangle face plus its edges, not its bounding box.
        box = world.trace_box([4.5,.5,3],[4.5,.5,-1],mins=(-.1,-.1,0),maxs=(.1,.1,.4),contents_mask=1)
        self.assertAlmostEqual(box['position'][2], .6)
        self.assertEqual(box['kind'], 'triangle')
        self.assertFalse(world.trace_box([5.8,1.8,3],[5.8,1.8,-1],
                         mins=(-.1,-.1,0),maxs=(.1,.1,.4),contents_mask=1)['hit'])

    @unittest.skipUnless((PACKAGE / 'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_actual_brush_ground_and_triangle_surface_are_consumed(self):
        from match_server.collision import CollisionWorld
        g = actual_geometry()
        world = CollisionWorld(g)
        # Authored DM spawn 79, supported by world brush 7537's z=4 face.
        ground = world.ground_point([3024,-826,48])
        self.assertEqual(ground['position'], [3024,-826,4])
        self.assertEqual((ground['kind'],ground['index']), ('brush',7537))
        self.assertFalse(ground['safe_spawn'])
        self.assertFalse(ground['start_solid'])
        box = world.trace_box([3024,-826,48],[3024,-826,-20])
        self.assertEqual(box['position'], [3024,-826,4])
        self.assertEqual(box['normal'], [0,0,1])
        self.assertFalse(box['start_solid'])
        # Resting on a flat brush does not obstruct a horizontal sweep.
        slide = world.trace_box([3024,-826,4],[3025,-826,4])
        self.assertFalse(slide['hit'])
        self.assertEqual(slide['position'], [3025,-826,4])
        stuck = world.trace_box([3024,-826,3],[3025,-826,3])
        self.assertTrue(stuck['start_solid'])
        dm = [p for p in json.loads((PACKAGE/'spawns.json').read_text()) if p['classname'] == 'mp_dm_spawn']
        self.assertEqual(len(dm),17)
        for point in dm:
            x,y,z = point['origin']
            hit = world.trace_box([x,y,z],[x,y,z-512])
            self.assertEqual(hit['position'], [x,y,4])
            self.assertFalse(hit['start_solid'])
            self.assertEqual(hit['unresolved_static_models'], [])
        # Terrain-only consumer, triangle 0 lies in y=-3408. AABB proximity
        # alone cannot certify the x/z barycentric containment below.
        terrain = CollisionWorld(dict(g,world_brushes=[]))
        hit = terrain.trace_point([-1264.5,-3410,9],[-1264.5,-3406,9],contents_mask=0xffffffff)
        self.assertTrue(hit['hit'])
        self.assertEqual(hit['position'], [-1264.5,-3408,9])
        self.assertEqual(hit['kind'], 'triangle')
        box = terrain.trace_box([-1264.5,-3410,9],[-1264.5,-3406,9],
                                mins=(-.1,-.1,-.1),maxs=(.1,.1,.1),contents_mask=0xffffffff)
        self.assertAlmostEqual(box['position'][1], -3408.1)
        self.assertEqual(box['kind'], 'triangle')

    @unittest.skipUnless((PACKAGE / 'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_partition_block_and_broken_shared_reference_are_not_silently_ignored(self):
        data = bytearray((PACKAGE / 'collision.bin').read_bytes())
        world = (PACKAGE / 'gfxworld.bin').read_bytes()
        sections = exporter.read_collision(data)['sections']
        # Synthetic change on licensed fixture: first partition uses block 1.
        data[sections['partitions']['offset']+2] = 1
        changed = exporter.read_geometry(data,world)
        self.assertEqual(changed['triangles'][0], [1024+i for i in actual_geometry()['triangles'][0]])
        struct.pack_into('<I',data,sections['brush_sides']['offset'],0x30104c4a)
        with self.assertRaisesRegex(ValueError, 'shared plane'):
            exporter.read_geometry(data,world)

    @unittest.skipUnless((PACKAGE / 'gfxworld.bin').is_file(), 'local map export unavailable')
    def test_actual_shared_planes_and_partition_geometry_are_resolved(self):
        g = actual_geometry()
        self.assertEqual(len(g['planes']), 7204)
        self.assertEqual(len(g['brushes']), 14931)
        self.assertEqual(len(g['sides']), 18960)
        self.assertEqual(len(g['triangles']), 11610)
        self.assertEqual(len(g['vertices']), 5319)
        self.assertEqual({p['vert_block'] for p in g['partitions']}, {0})
        self.assertTrue(g['world_brushes'])
        self.assertTrue(g['world_partitions'])
        self.assertFalse(g['physics_ready'])
        self.assertEqual(len(g['static_models']), 1627)
        self.assertEqual(g['closure']['unresolved_static_models'], 1627)


if __name__ == '__main__':
    unittest.main()
