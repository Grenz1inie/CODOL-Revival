"""Public version detection/selection contract; all game files are disposable."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from manager.installations import Installations


class InstallationsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / '游戏目录 with spaces'
        (self.game / 'IIPS').mkdir(parents=True)
        (self.game / 'TCLS').mkdir()
        (self.game / 'IIPS/IIPSVersion.ini').write_text('3.3.3.3', encoding='utf-8-sig')
        (self.game / 'TCLS/mmog_data.xml').write_text('<VersionUpdateData><ClientConf><VersionData><Version>3.3.3.3</Version></VersionData></ClientConf></VersionUpdateData>')
        (self.game / 'client.exe').write_bytes(b'known client')
        self.catalog = [{'game_id': 'codol', 'version': '3.3.3.3', 'adapter': 'games.codol.versions.v3_3_3_3.adapter',
                         'executable': 'client.exe', 'sha256': hashlib.sha256(b'known client').hexdigest()},
                        {'game_id': 'codol', 'version': '2.6.9.7', 'adapter': None, 'executable': 'client.exe'}]
        self.manager = Installations(self.root, catalog=self.catalog)

    def test_selection_identifies_persists_and_rechecks_without_touching_game(self):
        before = {p: p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        self.assertEqual(self.manager.current()['state'], 'unselected')
        selected = self.manager.select(str(self.game))
        self.assertEqual(selected['state'], 'matched')
        self.assertEqual(selected['version'], '3.3.3.3')
        self.assertEqual(selected['path'], str(self.game.resolve()))
        self.assertEqual(Installations(self.root, catalog=self.catalog).current(), selected)
        self.assertEqual(before, {p: p.read_bytes() for p in self.game.rglob('*') if p.is_file()})
        (self.game / 'client.exe').write_bytes(b'changed executable')
        self.assertEqual(self.manager.current()['state'], 'fingerprint_mismatch')

    def test_detection_covers_version_files_and_never_uses_directory_name(self):
        ini = self.game / 'IIPS/IIPSVersion.ini'
        xml = self.game / 'TCLS/mmog_data.xml'
        cases = [
            ('3.3.3.3', None, 'matched'),
            (None, '3.3.3.3', 'matched'),
            ('3.3.3.3', '2.6.9.7', 'invalid'),
            ('2.6.9.7', '2.6.9.7', 'unsupported'),
            ('9.9.9.9', '9.9.9.9', 'unknown'),
            ('broken', None, 'invalid'),
            (None, None, 'invalid'),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                if left is None: ini.unlink(missing_ok=True)
                else: ini.write_text(left)
                if right is None: xml.unlink(missing_ok=True)
                else: xml.write_text(f'<VersionUpdateData><ClientConf><VersionData><Version>{right}</Version></VersionData></ClientConf></VersionUpdateData>')
                self.assertEqual(self.manager.detect(str(self.game))['state'], expected)
        self.assertFalse(self.manager.file.exists())

    def test_original_gb2312_xml_and_missing_or_unreadable_inputs(self):
        xml = self.game / 'TCLS/mmog_data.xml'
        xml.write_bytes(('<?xml version="1.0" encoding="gb2312"?>\n'
                         '<VersionUpdateData><!--体验服--><ClientConf><VersionData>'
                         '<Version>3.3.3.3</Version></VersionData></ClientConf></VersionUpdateData>').encode('gb2312'))
        self.assertEqual(self.manager.detect(str(self.game))['state'], 'matched')
        xml.write_text('<broken')
        self.assertEqual(self.manager.detect(str(self.game))['state'], 'invalid')
        xml.unlink()
        (self.game / 'client.exe').unlink()
        self.assertEqual(self.manager.detect(str(self.game))['state'], 'invalid')
        self.assertEqual(self.manager.detect(str(self.game / 'missing'))['state'], 'invalid')

    def test_invalid_selection_disables_previous_match_and_paths_isolate_instances(self):
        selected = self.manager.select(str(self.game))
        first_runtime = self.manager.runtime(selected)
        self.assertTrue(first_runtime.is_relative_to(self.root / 'runtime/instances'))
        import shutil
        other = self.game.with_name('另一份安装')
        shutil.copytree(self.game, other)
        self.assertNotEqual(first_runtime, self.manager.runtime(self.manager.select(str(other))))
        self.assertEqual(self.manager.select(str(self.root / 'absent'))['state'], 'invalid')
        self.assertEqual(self.manager.current()['state'], 'invalid')
        self.assertFalse(first_runtime.exists())

    def test_invalid_api_values_and_corrupt_saved_selection_are_safe(self):
        for path in (None, 1, '', '  '):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.manager.select(path)
        self.manager.file.parent.mkdir()
        self.manager.file.write_text('not json')
        self.assertEqual(self.manager.current()['state'], 'invalid')


if __name__ == '__main__':
    unittest.main()
