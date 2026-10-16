"""Native registration/model selection; asset loading and rendering are excluded."""
import unittest

from client_reader423 import ClientReader423


class MatchComposedWeaponTests(unittest.TestCase):
    def setUp(self):
        self.client = ClientReader423()
        # Only slot 5 matters to this seam. Other names stand in for the 350
        # published base slots; no runtime package or running game is required.
        rows = [('none', '', '', 0, 0, '', 0, '', '')]
        rows += [(('acr_mp' if i == 5 else f'base_{i}'), f'ammo_{i}',
                  f'clip_{i}', 0, 0, '', 0, '', '') for i in range(1, 352)]
        # ACR's observed 0x6b0/0xd68/0xd69/0xd6a/0xdad bytes are all zero.
        self.assertIsNotNone(self.client.weapon_registry(rows))

    def test_recipe_gets_slot_352_base_ammo_5_and_own_clip_352(self):
        result = self.client.register_composed_weapon(base=5, name='** 5 0 0')
        self.assertEqual(result['weapon'], 352)
        self.assertEqual((result['ammo'], result['clip']), (5, 352))
        self.assertEqual(result['name'], '** 5 0 0')
        self.assertEqual(result['base_name'], 'acr_mp')
        self.assertEqual(result['base_keys'], (5, 5))

    def test_composed_viewmodel_is_appended_instead_of_tag_origin(self):
        result = self.client.register_composed_weapon(base=5, name='** 5 0 0')
        missing = self.client.composed_viewmodels(result['definition'], view_model=None)
        self.assertEqual(missing['models'], ['viewhands_player_tf141'])
        self.assertFalse(missing['appended'])
        # Live CSV camo 0: acr_mp,0,wea_acr_acr_blk,wea_acr_acr_blk_vmgun.
        # This supplies the resolved asset boundary, not a mock CSV consumer.
        selected = self.client.composed_viewmodels(
            result['definition'], view_model='wea_acr_acr_blk_vmgun')
        self.assertTrue(selected['appended'])
        self.assertEqual(selected['fallback'], 'tag_origin')
        self.assertEqual(selected['models'],
                         ['viewhands_player_tf141', 'wea_acr_acr_blk_vmgun'])
        self.assertNotIn('tag_origin', selected['models'])


if __name__ == '__main__':
    unittest.main()
