"""Restored publisher data must populate the shipped client's menu records."""
from pathlib import Path
import unittest

from client_playlist423 import ClientPlaylist423


class PlaylistTests(unittest.TestCase):
    def test_nuketown_reuses_existing_team_category_without_new_tab(self):
        reader=ClientPlaylist423()
        content=(Path(__file__).resolve().parents[1]/'data/match-playlist.info').read_text('utf-8').encode('gbk')
        visible={item['id']:item for item in reader.parse(content) if item['playlists']}
        self.assertNotIn(6,visible)
        self.assertFalse(any(240 in item['playlists'] for item in visible.values()))
        self.assertEqual(visible[1]['name'],'冲锋团队竞技')
        self.assertIn(110,visible[1]['playlists'])
        entry=reader.playlist(110)
        self.assertEqual(entry['name'],'-核弹小镇')
        self.assertEqual(entry['maps'],[('mp_nuked','ffa')])
        self.assertIn('一名真人',entry['description'])
        self.assertIn('自由混战',entry['description'])
        self.assertNotIn('9V9',entry['description'])

    def test_stock_categories_and_map_choices_reach_client(self):
        reader=ClientPlaylist423()
        content=(Path(__file__).resolve().parents[1]/'data/match-playlist.info').read_text('utf-8').encode('gbk')
        categories=reader.parse(content)
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
