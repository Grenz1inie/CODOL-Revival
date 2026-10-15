import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
HEADERS=ROOT/'research/experiments/story-native/reference-zone-assets/current-common_mp-weapons.json'


class MatchLoadoutTests(unittest.TestCase):
    def test_nuketown_bundle_requires_its_registry_and_preserves_navigation(self):
        from export_match_loadout import export_loadout
        from match_server.mapdata import load_map
        from match_server.navigation import Navigation
        base = ROOT / 'research/experiments/independent-match'
        package = base / 'nuketown-dm-v1'
        registration = base / 'nuketown-registration-v1'
        zone = ROOT / 'research/experiments/story-native/zone-assets/common_mp/zone.bin'
        waypoint = ROOT.parent / 'sh1x_dedicated/bin/home/main/waypoints/mp_nuked_wp.csv'
        if not all(p.exists() for p in (package/'manifest.json', registration/'ncs.json', zone, waypoint)):
            self.skipTest('local Nuketown resources unavailable')
        with tempfile.TemporaryDirectory(dir=base) as folder:
            with self.assertRaisesRegex(ValueError, 'selected map'):
                export_loadout(package, Path(folder)/'wrong', zone, waypoint, base/'registration/rebuilt')
            output = Path(folder)/'match'
            export_loadout(package, output, zone, waypoint, registration)
            data = load_map(output)
            loadout = json.loads(data['files']['loadout.json'])
            self.assertEqual(data['manifest']['map'], 'mp_nuked')
            self.assertEqual(loadout['weapon']['name'], 'acr_mp')
            self.assertEqual(data['files']['waypoints.csv'], waypoint.read_bytes())
            self.assertEqual(len(Navigation.from_csv(waypoint.read_text(), None).nodes), 235)
            self.assertEqual(loadout['provenance']['waypoint_source'], str(waypoint.resolve()))
            self.assertFalse(data['ncs']['mounted_set_verified'])
            self.assertEqual(data['ncs']['selected_zones'][11:13], ['mp_nuked', 'mp_nuked_const'])

    def test_bundle_extracts_current_header_by_its_real_name_and_keeps_sources_unchanged(self):
        from export_match_loadout import export_loadout
        from match_server.mapdata import load_map
        import hashlib
        package=ROOT/'research/experiments/independent-match/killhouse-dm-v3'
        zone=ROOT/'research/experiments/story-native/zone-assets/common_mp/zone.bin'
        waypoint=ROOT/'research/experiments/story-native/source-startup-xygdjp3z/main/waypoints/mp_killhouse_sh_wp.csv'
        registration=ROOT/'research/experiments/independent-match/registration/rebuilt'
        if not all(p.exists() for p in (package/'manifest.json',zone,waypoint,registration/'ncs.json')):
            self.skipTest('local map/weapon source unavailable')
        original=(package/'manifest.json').read_bytes()
        with tempfile.TemporaryDirectory(dir=package.parent) as temporary:
            output=Path(temporary)/'match'
            export_loadout(package,output,zone,waypoint,registration)
            data=load_map(output)
            loadout=json.loads(data['files']['loadout.json'])
            self.assertEqual(loadout['weapon']['name'],'acr_mp')
            self.assertEqual(loadout['weapon']['index'],5)
            self.assertEqual(loadout['body']['name'],'mp_fullbody_juggernaut_explosive_so')
            self.assertEqual(loadout['body']['index'],109)
            self.assertEqual(loadout['hands']['index'],53)
            self.assertEqual(data['ncs']['client_checksum'],3852334052)
            self.assertFalse(data['ncs']['mounted_set_verified'])
            self.assertEqual(data['files']['baseline.bin'],(package/'baseline.bin').read_bytes())
            header=bytes.fromhex(json.loads(HEADERS.read_text())['acr_mp'])
            self.assertEqual(data['files']['weapon-acr.bin'],header)
            self.assertEqual(data['files']['waypoints.csv'],waypoint.read_bytes())
            self.assertEqual(loadout['provenance']['weapon_header_sha256'],hashlib.sha256(header).hexdigest())
        self.assertEqual((package/'manifest.json').read_bytes(),original)

    @unittest.skipUnless(HEADERS.is_file(),'local current-client weapon fixture unavailable')
    def test_current_acr_header_supplies_combat_parameters_without_legacy_layout(self):
        from match_server.loadout import read_weapon
        header=bytes.fromhex(json.loads(HEADERS.read_text())['acr_mp'])
        weapon=read_weapon(header,index=5)
        self.assertEqual((weapon.index,weapon.ammo_type,weapon.clip_type),(5,5,5))
        self.assertEqual((weapon.clip_size,weapon.fire_ms,weapon.reload_ms,weapon.empty_reload_ms),
                         (36,90,2000,2500))
        self.assertEqual((weapon.damage,weapon.minimum_damage,
                          weapon.full_damage_range,weapon.minimum_damage_range),(30,22,1500,1501))
        for offset,value,code in ((0xd68,1,'B'),(0xbb8,20,'I'),(0xd10,0,'I'),(0xbcc,float('nan'),'f')):
            changed=bytearray(header)
            struct.pack_into('<'+code,changed,offset,value)
            with self.assertRaises(ValueError):
                read_weapon(changed,index=5)
        with self.assertRaises(ValueError):
            read_weapon(header[:-4],index=5)


if __name__=='__main__':
    unittest.main()
