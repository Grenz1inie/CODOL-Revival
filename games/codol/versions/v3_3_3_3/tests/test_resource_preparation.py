"""First-run resource inputs and publication, independent of research artifacts."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
import zlib

VERSION = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VERSION / 'reverse/tools'))
from reference_match.navigation import Navigation


class ResourcePreparationTests(unittest.TestCase):
    def test_distributed_inputs_preserve_verified_registration_and_navigation(self):
        resources = VERSION / 'resources'
        registration = json.loads((resources / 'definitions/network-registration423.json').read_text())
        self.assertEqual(registration['checksum_seed'], 3451066449)
        self.assertEqual(zlib.crc32(''.join(registration['names']).encode('ascii')), 3451066449)
        self.assertEqual(registration['exe_sha256'],
                         'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b')
        self.assertNotIn('pid', registration)
        self.assertNotIn('image_base', registration)
        data = (resources / 'navigation/mp_nuked_wp.csv').read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'dae775b788537a20e64b72524eecf1847f40f02e7a1070a69687441f77d69807')
        self.assertEqual(len(Navigation.from_csv(data.decode('ascii'), None).nodes), 235)


if __name__ == '__main__':
    unittest.main()
