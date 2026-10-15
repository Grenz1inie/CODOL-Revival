"""Restored publisher data must populate the shipped client's menu records."""
from pathlib import Path
import unittest

from client_playlist423 import ClientPlaylist423


class PlaylistTests(unittest.TestCase):
    def test_stock_categories_and_map_choices_reach_client(self):
        reader=ClientPlaylist423()
        categories=reader.parse((Path(__file__).resolve().parents[1]/'data/match-playlist.info').read_bytes())
        visible={item['id']:item for item in categories if item['playlists']}
        self.assertTrue({1,2,3,9,11,13,14,15,16}.issubset(visible), 'PVP categories missing')
        self.assertTrue({20,22,23,26,28,29,30}.issubset(visible), 'PVE categories missing')
        self.assertEqual(visible[3]['name'],'战术团队竞技')
        self.assertIn(13,visible[3]['playlists'])
        tdm=reader.playlist(13)
        self.assertEqual(tdm['name'],'战术团竞6V6')
        self.assertTrue(tdm['description'])
        self.assertIn(('mp_killhouse_sh','tdm'),tdm['maps'])
        self.assertEqual(len(tdm['maps']),34)
        for item in visible.values():
            self.assertTrue(item['name'])
            for playlist_id in item['playlists']:
                with self.subTest(playlist=playlist_id):
                    entry=reader.playlist(playlist_id)
                    self.assertTrue(entry['name'])
                    self.assertTrue(entry['description'])
                    self.assertTrue(entry['maps'])


if __name__=='__main__':
    unittest.main()
