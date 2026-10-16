"""Independent map export boundaries; no engine processes or generated fixtures."""
import importlib.util
from pathlib import Path
import sys
import struct
import hashlib
import json
import tempfile
from functools import lru_cache
from collections import Counter
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools'))
import export_match_map as exporter

STAGE = ROOT / 'research/experiments/story-native'
CLIENT = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'


@lru_cache(maxsize=2)
def actual_zone(name):
    from decode_story_fastfile import decode
    return decode(CLIENT.read_bytes(), (STAGE / 'startup-assets/chinese' / (name + '.ff')).read_bytes(), name)


def zone_fixture(assets):
    header = bytearray(56)
    struct.pack_into('<I', header, 20, 4096)  # persistent block 3 capacity
    struct.pack_into('<4I', header, 40, 0, 0, len(assets), 0xffffffff)
    end = 56 + len(assets) * 16
    directory = bytearray()
    for kind, payload in assets:
        directory.extend(struct.pack('<4I', kind, end - 40, 0xffffffff, len(payload)))
        end += len(payload)
    struct.pack_into('<I', header, 0, end - 40)
    return bytes(header + directory) + b''.join(data for _, data in assets)


class MatchMapExportTests(unittest.TestCase):
    def test_network_position_window_ignores_scenery_but_rejects_wide_entity_positions(self):
        from reference_match.snapshot import encode_player_entity
        state = bytearray(272)
        struct.pack_into('<ii', state, 0, 99, 6)
        struct.pack_into('<3f', state, 24, 100, 200, 300)
        geometry = dict(vertices=[[-100000, 0, 0], [100000, 0, 0]], brushes=[], static_models=[])
        spawns = [dict(classname='mp_dm_spawn', origin=[0, 0, 0]),
                  dict(classname='mp_sd_spawn_attacker', origin=[100000, 0, 0])]
        result = exporter.select_position(geometry, spawns, baseline=b'IWCB000\x01' + state,
                                          navigation=[[400, 0, 0]])
        self.assertEqual(result['position_base'], [200, 100, 150])
        self.assertTrue(result['network_positions_encodable'])
        value = struct.unpack('<I', struct.pack('<f', 40000))[0]
        with self.assertRaisesRegex(ValueError, 'position outside'):
            encode_player_entity({24: value}, position_base=result['position_base'])
        struct.pack_into('<f', state, 24, 70000)
        result = exporter.select_position(geometry, spawns, baseline=b'IWCB000\x01' + state)
        self.assertFalse(result['network_positions_encodable'])
        self.assertIsNone(result['position_base'])

    def test_unclassified_inline_model_in_dm_baseline_blocks_readiness(self):
        state = bytearray(272)
        struct.pack_into('<ii', state, 0, 99, 6)
        struct.pack_into('<I', state, 0x98, 1)
        report = dict(placements=[dict(submodel=1, category='script_state_unresolved', fields={})])
        self.assertEqual(exporter.select_dm_submodels(report, b'IWCB000\x01' + state, {}), [])
        self.assertEqual(len(report['blockers']), 1)
        self.assertIn('*1', report['blockers'][0])

    def test_selected_map_controls_assets_baseline_and_manifest(self):
        from unittest.mock import patch
        name = 'mp_nuked'
        baseline = b'IWCB000\x01' + struct.pack('<ii', 99, 6) + bytes(264)
        filename = f'mp/constbaselines/bl_pc_{name}_dm.bin'
        raw = struct.pack('<4I', 0xffffffff, 0, len(baseline), 0xffffffff)
        raw += filename.encode() + b'\0' + baseline
        zones = {name: zone_fixture([(15, b'clip'), (21, b'world')]),
                 name + '_const': zone_fixture([(36, raw)])}
        collision = dict(checksum=123, sections={}, entity_text=b'{\n"classname" "worldspawn"\n}\n\0')
        with tempfile.TemporaryDirectory(dir=exporter.OUTPUT_ROOT) as folder:
            output = Path(folder) / 'map'
            with patch.object(exporter, 'read_collision', return_value=collision), \
                    patch.object(exporter, 'enrich_geometry'):
                report = exporter.export_zones(zones, output, map_name=name)
            self.assertEqual(report['map'], name)
            self.assertEqual(report['baseline']['name'], filename)
            self.assertEqual((output / 'baseline.bin').read_bytes(), baseline)
            self.assertEqual((output / 'collision.bin').read_bytes(), b'clip')
            ncs = json.loads((output / 'ncs.json').read_text())
            self.assertNotIn(name, ncs['missing_candidate_zones'])
            self.assertNotIn('mp_killhouse_sh', ncs['missing_candidate_zones'])
            self.assertFalse(ncs['mounted_set_verified'])

    def test_prefix_string_api_reuses_ncs_replay_and_rejects_unreplayed_pointers(self):
        table = struct.pack('<5I',0xffffffff,0,0,1,0xffffffff)+b'ncs\0'+struct.pack('<I',0xffffffff)+b'acr_mp\0'
        zone = zone_fixture([(44,table),(28,b'weapon header excluded')])
        block = exporter.read_ncs_prefix_block3(zone)
        offset = block.index(b'acr_mp\0')
        self.assertEqual(exporter.read_block3_string(block,0x30000001+offset), 'acr_mp')
        with self.assertRaises(ValueError):
            exporter.read_block3_string(block,0x30000001+len(block))
        with self.assertRaises(ValueError):
            exporter.read_block3_string(block,0x40000001+offset)

    @unittest.skipUnless(CLIENT.is_file() and (STAGE / 'startup-assets/chinese/mp_killhouse_sh_const.ff').is_file(),
                         'local licensed Killhouse resources unavailable')
    def test_export_is_self_contained_and_never_claims_client_ncs_or_complete_collision(self):
        spec = importlib.util.spec_from_file_location('mapdata', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/reference_match/mapdata.py')
        loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loader)
        zones = {n: actual_zone(n) for n in ('mp_killhouse_sh', 'mp_killhouse_sh_const')}
        parent = ROOT / 'research/experiments/independent-match'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            output = Path(folder) / 'map'
            report = exporter.export_zones(zones, output, gametype='dm')
            loaded = loader.load_map(output)
            self.assertEqual(len(loaded['baselines']), 156)
            # The first authored state is entity 99, not ordinal zero.
            self.assertEqual(struct.unpack_from('<i', loaded['baselines'][0])[0], 99)
            self.assertEqual(report['map_checksum'], 0xbd5616d7)
            self.assertFalse(loaded['collision']['physics_ready'])
            self.assertFalse(loaded['collision']['static_model_geometry_exported'])
            self.assertIsNone(loaded['ncs']['client_checksum'])
            self.assertIsNone(loaded['ncs']['registry'])  # No seed was supplied.
            self.assertFalse(loaded['ncs']['mounted_set_verified'])
            self.assertIn('common_mp', loaded['ncs']['missing_candidate_zones'])
            self.assertEqual(report['inputs'][0]['zone_sha256'], hashlib.sha256(zones['mp_killhouse_sh']).hexdigest())
            self.assertEqual(loaded['manifest']['runtime_dependencies'], [])
            position = loaded['position']
            self.assertEqual(position['status'], 'server_selected')
            self.assertEqual(position['center'], [1859,-80,2083])
            self.assertEqual(position['position_base'], [1859,-80,2083])
            self.assertTrue(position['client423_verified'])
            self.assertTrue(position['network_positions_encodable'])
            self.assertEqual(report['position_status'], 'server_selected')
            self.assertIn('position.json', report['files'])
            baseline = output / 'baseline.bin'
            baseline.write_bytes(baseline.read_bytes()[:-1])
            with self.assertRaisesRegex(ValueError, 'integrity'):
                loader.load_map(output)

    @unittest.skipUnless(CLIENT.is_file() and (STAGE / 'startup-assets/chinese/mp_killhouse_sh_const.ff').is_file(),
                         'local licensed Killhouse resources unavailable')
    def test_registration_seed_evidence_never_proves_actual_client_checksum(self):
        registration = json.loads((ROOT / 'research/evidence/live-netconst-registration423.json').read_text())
        zones = {n: actual_zone(n) for n in ('mp_killhouse_sh', 'mp_killhouse_sh_const')}
        parent = ROOT / 'research/experiments/independent-match'
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent) as folder:
            target = Path(folder) / 'valid'
            exporter.export_zones(zones, target, registration=registration)
            ncs = json.loads((target / 'ncs.json').read_text())
            self.assertEqual(ncs['checksum_seed'], 3451066449)
            self.assertEqual(ncs['status'], 'offline_candidate_only')
            self.assertIsInstance(ncs['registry']['checksum'], int)
            self.assertIsNone(ncs['client_checksum'])
            self.assertFalse(ncs['client_checksum_verified'])
            self.assertFalse(ncs['mounted_set_verified'])
            for overrides in ({'checksum_seed': 0}, {'exe_sha256': 'wrong'}):
                bad_target = Path(folder) / 'bad'
                with self.assertRaisesRegex(ValueError, 'registration evidence'):
                    exporter.export_zones(zones, bad_target, registration=dict(registration, **overrides))
                self.assertFalse(bad_target.exists())

    @unittest.skipUnless(CLIENT.is_file() and (STAGE / 'startup-assets/chinese/mp_killhouse_sh.ff').is_file(),
                         'local licensed Killhouse resources unavailable')
    def test_actual_killhouse_sections_and_authored_spawns(self):
        asset = next(data for kind, data in exporter.read_assets(actual_zone('mp_killhouse_sh')) if kind == 15)
        result = exporter.read_collision(asset)
        self.assertEqual(result['checksum'], 0xbd5616d7)
        self.assertEqual(result['map_entities_offset'], 2297450)
        self.assertEqual(result['entity_text_size'], 99955)
        sections = result['sections']
        self.assertEqual((sections['brushes']['count'], sections['brushes']['offset']), (14931, 759738))
        self.assertEqual((sections['triangles']['count'], sections['triangles']['stride']), (11610, 6))
        self.assertEqual(sections['static_models']['count'], 1627)
        self.assertIsNone(sections['planes']['offset'])
        self.assertEqual(sections['planes']['reference'], 0x30104c49)
        counts = Counter(p['classname'] for p in exporter.read_spawns(result['entity_text']))
        self.assertEqual(counts['mp_dm_spawn'], 17)
        self.assertEqual(counts['mp_tdm_spawn_allies_start'], 18)
        self.assertEqual(counts['mp_tdm_spawn_axis_start'], 17)
        for bad in (asset[:255], asset[:1000000], asset[:2297500]):
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                exporter.read_collision(bad)
        damaged = bytearray(asset)
        struct.pack_into('<I', damaged, 2297450 + 8, 0xffffffff)
        with self.assertRaises(ValueError):
            exporter.read_collision(damaged)

    def test_ncs_replay_resolves_previous_table_strings_and_reports_unhandled_assets(self):
        first = struct.pack('<5I', 0xffffffff, 0, 1, 1, 0xffffffff)
        first += b'first\0' + struct.pack('<I', 0xffffffff) + b'alpha\0'
        second = struct.pack('<5I', 0xffffffff, 1, 1, 1, 0xffffffff)
        second += b'second\0' + struct.pack('<I', 0x3000002d)
        result = exporter.read_zone_ncs(zone_fixture([(44, first), (44, second)]))
        self.assertEqual([t['strings'] for t in result['tables']], [['alpha'], ['alpha']])
        self.assertEqual(result['unresolved'], [])
        bad = second[:-4] + struct.pack('<I', 0x3000ffff)
        result = exporter.read_zone_ncs(zone_fixture([(44, first), (44, bad)]))
        self.assertEqual(len(result['unresolved']), 1)
        late = exporter.read_zone_ncs(zone_fixture([(36, b''), (44, first)]))
        self.assertEqual(late['tables'], [])
        self.assertIn('non-prefix', late['unresolved'][0]['reason'])

    def test_spawn_points_preserve_map_order_and_do_not_include_worldspawn(self):
        text = (b'{"classname" "worldspawn"}\n'
                b'{"classname" "mp_dm_spawn" "origin" "12 -4 53" "angles" "0 180 0"}\n'
                b'{"classname" "mp_tdm_spawn_axis_start" "origin" "1 2 3" "angles" "0 90 0"}\0')
        points = exporter.read_spawns(text)
        self.assertEqual([p['entity_index'] for p in points], [1, 2])
        self.assertEqual(points[0]['origin'], [12.0, -4.0, 53.0])
        self.assertEqual(points[1]['angles'], [0.0, 90.0, 0.0])
        for bad in (text[:-1], text.replace(b'12 -4 53', b'nan 0 0'),
                    text.replace(b'"angles" "0 180 0"', b''), text.replace(b'}\n', b'\n', 1)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                exporter.read_spawns(bad)


if __name__ == '__main__':
    unittest.main()
