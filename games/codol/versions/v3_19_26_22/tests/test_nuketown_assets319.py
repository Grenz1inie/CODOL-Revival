import unittest
from games.codol.versions.v3_19_26_22.client.nuketown_assets import select_spawn


class NuketownAssetsTests(unittest.TestCase):
    def test_selects_team_spawn_and_preserves_current_resource_coordinates(self):
        text = ('{\n"classname" "worldspawn"\n}\n'
                '{\n"classname" "mp_dm_spawn"\n"origin" "9 9 9"\n}\n'
                '{\n"classname" "mp_tdm_spawn"\n"origin" "-1601.8 1176.2 -24"\n'
                '"angles" "0 330 0"\n}\n').encode()+b'\0'
        self.assertEqual(select_spawn(text), {'map':'mp_nuked', 'origin':[-1601.8,1176.2,-24.0],
                                             'yaw':330.0, 'classname':'mp_tdm_spawn'})

    def test_missing_or_malformed_spawn_never_falls_back_to_another_map(self):
        for text in [b'', b'{"classname" "worldspawn"}\0',
                     b'{"classname" "mp_tdm_spawn" "origin" "1 2" "angles" "0 0 0"}\0',
                     b'{"classname" "mp_tdm_spawn" "origin" "NaN 2 3" "angles" "0 0 0"}\0',
                     b'{"classname" "mp_tdm_spawn" "origin" "1 2 3"}\0',
                     b'{"classname" "mp_tdm_spawn" "origin" "1 2 3" "angles" "0 0 0"}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                select_spawn(text)


if __name__ == '__main__': unittest.main()
