"""File-boundary contract recovered from client 0x5849f0/0x46c250."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


class StoryBaselineTests(unittest.TestCase):
    def test_real_first_map_and_client_rejection_boundaries(self):
        spec = importlib.util.spec_from_file_location('index_story_zone', ROOT / 'tools/index_story_zone.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = (ROOT / 'research/experiments/story-native/zone-assets/coop_training_mp_cargoship_const/0.raw').read_bytes()
        rows = module.read_baselines(raw)
        self.assertEqual(len(rows), 700)
        self.assertEqual((rows[0]['entity_id'], rows[-1]['entity_id']), (27, 813))
        self.assertEqual(rows[0]['state'], raw[8:280])
        self.assertEqual(module.read_baselines(raw[:8]), [])
        edge = raw[:8] + struct.pack('<ii', 2048, 0) + bytes(264)
        self.assertEqual(module.read_baselines(edge)[0]['entity_id'], 2048)
        bad = [b'', raw[:-1], raw + bytes(272), b'BADMAGIC' + raw[8:]]
        for offset, value in ((8, -1), (8, 2049), (12, -1)):
            changed = bytearray(raw)
            struct.pack_into('<i', changed, offset, value)
            bad.append(changed)
        for i, wire in enumerate(bad):
            with self.subTest(case=i), self.assertRaises(ValueError):
                module.read_baselines(wire)


if __name__ == '__main__':
    unittest.main()
