"""Rebuild both registration sets from signed current-client fastfiles."""
import unittest
from pathlib import Path

from build_match_registration import build
from probe_match_registration import RegistrationProbe

ROOT = Path(__file__).resolve().parents[5]


class BuildMatchRegistrationTests(unittest.TestCase):
    def test_signed_fastfiles_reproduce_both_native_registration_checksums(self):
        result = build(
            ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe',
            ROOT / 'research/experiments/story-native/startup-assets/chinese',
            ROOT / 'research/evidence/live-netconst-registration423.json')
        for name, crc in [('frontend', 962763178), ('map', 3852334052)]:
            data = result[name]
            self.assertEqual(data['registry']['checksum'], crc)
            self.assertEqual(RegistrationProbe().build_registration(
                data['tables'], data['registration_evidence']),
                dict(checksum=crc, registered=1))
            self.assertFalse(data['mounted_set_verified'])
        self.assertEqual(len(result['map']['tables']), 54)
        self.assertIn('ncs_mdl_common_marketplace_lite', result['map']['registry']['table_order'])
        self.assertNotIn('ui_mp', result['map']['selected_zones'])
        self.assertIn('ui_mp', result['frontend']['selected_zones'])


if __name__ == '__main__':
    unittest.main()
