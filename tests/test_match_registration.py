"""Current-client registration and map mount contracts, no game process."""
import json
from pathlib import Path
import unittest

from probe_match_registration import RegistrationProbe
from story_netconst423 import build_registry

ROOT = Path(__file__).resolve().parents[1]


class MatchRegistrationTests(unittest.TestCase):
    def test_complete_loader_set_passes_actual_build_sort_and_registration(self):
        data = json.loads((ROOT / 'research/experiments/independent-match/registration/ncs.json').read_text())
        probe = RegistrationProbe()
        registration = json.loads((ROOT / 'research/evidence/live-netconst-registration423.json').read_text())
        result = probe.build_registration(list(reversed(data['tables'])), registration)
        self.assertEqual(result, dict(checksum=3852334052, registered=1))

    def test_frontend_market_survives_ui_unload_and_map_uses_flag_four(self):
        probe = RegistrationProbe()
        frontend = probe.zone_records('frontend')
        flags = {r['name']: r['alloc'] for r in frontend if r['name']}
        self.assertEqual(flags['common_marketplace_lite'], 1)
        self.assertEqual(flags['localized_common_marketplace_lite'], 1)
        self.assertEqual(flags['common_mp'], 1)
        self.assertEqual(flags['ui_mp'], 2)
        load = probe.zone_records('loadscreen', flags=3)
        self.assertEqual(load[0], dict(name=None, alloc=0, free=0x1a, sync=0))
        self.assertEqual([r['name'] for r in load[1:]], ['mp_killhouse_sh_load', 'common_loadscreen'])
        self.assertTrue(all(r['alloc'] == 8 for r in load[1:]))
        self.assertFalse(flags['common_marketplace_lite'] & load[0]['free'])
        self.assertTrue(flags['ui_mp'] & load[0]['free'])
        game = probe.zone_records('map', flags=15)
        self.assertEqual(game[0]['free'], 6)
        self.assertTrue(all(r['alloc'] == 4 for r in game[1:]))
        self.assertIn('mp_addon_mp_killhouse_sh', [r['name'] for r in game])

    def test_loadingnewmap_queues_local_upload_and_preserves_connection(self):
        for ready, state in ((False, 6), (True, 7)):
            result = RegistrationProbe().loading_message(db_ready=ready)
            self.assertEqual(result['command'], 'uploadStats\n')
            self.assertEqual(result['state'], state)
            self.assertEqual(result['map'], 'mp_killhouse_sh')
            self.assertEqual(result['category'], 'mp')
            self.assertEqual(result['registered'], 0)
            self.assertTrue(result['connection_unchanged'])

    def test_heartbeat_response_waits_for_both_db_events(self):
        for ready, state in ((False, 6), (True, 7)):
            self.assertEqual(RegistrationProbe().heartbeat_response(db_ready=ready), state)

    def test_actual_loader_requests_reload_patch_and_map_zones(self):
        result = RegistrationProbe().zone_plan('mp_killhouse_sh', 'mp')
        self.assertEqual(result, ['common_mp_reload', 'patch_common_gametype_mp',
            'common_gametype_mp', 'patch_localized_common_gametype_mp',
            'localized_common_gametype_mp', 'mp_addon_mp_killhouse_sh', 'patch_mp_killhouse_sh',
            'mp_killhouse_sh_const', 'mp_killhouse_sh'])

    def test_already_mounted_common_category_is_not_requested_again(self):
        result = RegistrationProbe().zone_plan('mp_killhouse_sh', 'mp',
                                               mounted={'common_gametype_mp'})
        self.assertEqual(result, ['common_mp_reload', 'mp_addon_mp_killhouse_sh', 'patch_mp_killhouse_sh',
                                  'mp_killhouse_sh_const', 'mp_killhouse_sh'])

    def test_candidate_crc_matches_actual_registrar_but_not_no_map_set(self):
        data = json.loads((ROOT / 'research/experiments/independent-match/killhouse-dm-v3/ncs.json').read_text())
        tables = data['tables']
        seed = data['checksum_seed']
        full = RegistrationProbe().register(tables, seed)
        self.assertEqual(full, build_registry(tables, checksum_seed=seed)['checksum'])
        without_map = [t for t in tables if not t['zone'].startswith('mp_killhouse_sh')]
        pre = RegistrationProbe().register(without_map, seed)
        self.assertNotEqual(pre, full)

    def test_loadingnewmap_resets_registry_and_marks_preload(self):
        probe = RegistrationProbe()
        self.assertEqual(probe.preload('mp_killhouse_sh', 'mp'),
                         dict(map='mp_killhouse_sh', category='mp', flags=[1, 1, 1], registered=0))


if __name__ == '__main__':
    unittest.main()
