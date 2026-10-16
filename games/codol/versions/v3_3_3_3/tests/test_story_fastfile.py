"""423 FF decoding at the file boundary, with current-client crypto metadata."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[5]


class StoryFastfileTests(unittest.TestCase):
    def test_first_map_decodes_and_rejects_corrupt_blocks(self):
        spec = importlib.util.spec_from_file_location('decode_story_fastfile', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/decode_story_fastfile.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        client = (ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe').read_bytes()
        manifest = json.loads((ROOT / 'research/experiments/story-native/resources/manifest.json').read_text())
        item = next(f for a in manifest['archives'] for f in a['files']
                    if f['name'].endswith('/coop_training_mp_cargoship.ff'))
        wire = (ROOT / item['file']).read_bytes()
        zone = module.decode(client, wire, 'coop_training_mp_cargoship')
        self.assertIn(b'coop_training_mp_cargoship', zone)
        constant = next(f for a in manifest['archives'] for f in a['files']
                        if f['name'].endswith('/coop_training_mp_cargoship_const.ff'))
        const_zone = module.decode(client, (ROOT / constant['file']).read_bytes(), 'coop_training_mp_cargoship_const')
        self.assertEqual(len(const_zone), 10488)
        with self.assertRaisesRegex(ValueError, 'map name'):
            module.decode(client, wire, 'another_map')
        for offset in (300, 0x2115 + 100, 0x4115 + 100):
            corrupt = bytearray(wire)
            corrupt[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                module.decode(client, bytes(corrupt), 'coop_training_mp_cargoship')


if __name__ == '__main__':
    unittest.main()
