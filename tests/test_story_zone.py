"""Current-version zone directory and resource reader boundaries."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StoryZoneTests(unittest.TestCase):
    def test_netconst_pooled_names_arrays_and_string_boundaries(self):
        spec = importlib.util.spec_from_file_location('index_story_zone', ROOT / 'tools/index_story_zone.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        block = b'ncs_pool\0alpha\0beta\0' + struct.pack('<2I', 0x3000000a, 0x30000010)
        mixed = struct.pack('<7I', 0x30000001, 0, 0, 2, 0xffffffff,
                            0x3000000a, 0xffffffff) + b'gamma\0'
        self.assertEqual(module.read_ncs(mixed, block)['strings'], ['alpha', 'gamma'])
        pooled = struct.pack('<5I', 0x30000001, 0, 0, 2, 0x30000015)
        self.assertEqual(module.read_ncs(pooled, block)['strings'], ['alpha', 'beta'])
        bad = [(mixed, None), (mixed[:-1], block), (mixed + b'x', block),
               (pooled, block[:-1]), (pooled, block[:20] + struct.pack('<2I', 0xffffffff, 0x30000010))]
        for pointer in (0, 0x20000001, 0x300000ff):
            bad.append((struct.pack('<I', pointer) + mixed[4:], block))
        for data, context in bad:
            with self.subTest(data=data, context=context), self.assertRaises(ValueError):
                module.read_ncs(data, context)

    def test_common_zone_keeps_zero_length_shared_asset_references(self):
        spec = importlib.util.spec_from_file_location('index_story_zone', ROOT / 'tools/index_story_zone.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        zone = (ROOT / 'research/experiments/story-native/zone-assets/common_mp/zone.bin').read_bytes()
        assets = module.read_assets(zone)
        self.assertEqual(len(assets), 9329)
        self.assertEqual(assets[1942], (5, b''))
        self.assertEqual(assets[3557], (40, b''))

    def test_directory_and_map_registration_keep_resource_order(self):
        spec = importlib.util.spec_from_file_location('index_story_zone', ROOT / 'tools/index_story_zone.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = json.loads((ROOT / 'research/evidence/story-ff427-decoded-zones.json').read_text())
        zone = (ROOT / report[0]['file']).read_bytes()
        assets = module.read_assets(zone)
        self.assertEqual(len(assets), 1174)
        registrations = [module.read_ncs(data) for kind, data in assets if kind == 44]
        vehicle = next(r for r in registrations if r['type'] == 2)
        self.assertEqual(vehicle['name'], 'ncs_veh_coop_training_mp_cargoship')
        self.assertEqual(vehicle['strings'], ['blackhawk', 'seaknight'])
        with self.assertRaises(ValueError):
            module.read_assets(zone[:-1])
        corrupt = bytearray(zone)
        corrupt[11542 + 4] ^= 1
        with self.assertRaises(ValueError):
            module.read_assets(corrupt)


if __name__ == '__main__':
    unittest.main()
