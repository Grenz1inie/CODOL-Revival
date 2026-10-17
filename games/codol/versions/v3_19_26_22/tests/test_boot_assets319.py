import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from games.codol.versions.v3_19_26_22.client import boot_assets


class BootAssetsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source, self.output = self.root/'original', self.root/'generated'
        hashes = {}
        for name in boot_assets.SOURCE_HASHES:
            path = self.source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.patcher = patch.dict(boot_assets.SOURCE_HASHES, hashes, clear=True)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_cached_generated_assets_are_checked_and_repaired_without_touching_profile(self):
        before = {str(p):p.read_bytes() for p in self.source.rglob('*') if p.is_file()}
        self.output.mkdir()
        profile = self.output/'profile319.json'
        profile.write_bytes(b'player progress')
        with patch.object(boot_assets, 'generate', return_value={'publisher-files/configs_s.info': b'generated'}) as build:
            self.assertEqual(boot_assets.build(self.source,self.output,self.root/'native'),self.output)
            boot_assets.build(self.source,self.output,self.root/'native')
            self.assertEqual(build.call_count,1)
            (self.output/'publisher-files/configs_s.info').write_bytes(b'damaged')
            boot_assets.build(self.source,self.output,self.root/'native')
            self.assertEqual(build.call_count,2)
        self.assertEqual(profile.read_bytes(),b'player progress')
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.source.rglob('*') if p.is_file()})

    def test_bad_original_or_failed_generation_cannot_publish_ready_outputs(self):
        with patch.object(boot_assets, 'generate', side_effect=ValueError('bad resource')):
            with self.assertRaisesRegex(ValueError,'bad resource'):
                boot_assets.build(self.source,self.output,self.root/'native')
        self.assertFalse((self.output/'boot-build.json').exists())
        (self.source/next(iter(boot_assets.SOURCE_HASHES))).write_bytes(b'wrong version')
        with patch.object(boot_assets,'generate') as build:
            with self.assertRaisesRegex(ValueError,'original'):
                boot_assets.build(self.source,self.output,self.root/'native')
            build.assert_not_called()
