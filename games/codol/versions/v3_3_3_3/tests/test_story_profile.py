"""Consume an exported v19 profile with the generated native storage reader."""
from pathlib import Path
import hashlib
import os
import subprocess
import tempfile
import unittest

from test_dw_progression import CAPTURE_V19, RAW_V19_SHA256, USER_ID, PrivateProfileStore

ROOT = Path(__file__).resolve().parents[5]


@unittest.skip('Blocked: Huorong quarantined story_profile.exe on 2026-10-15; '
               'resolve the detection before rebuilding this probe.')
class StoryProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='codol-profile-native-')
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name)
        cls.probe = cls.root / 'story_profile.exe'
        source = ROOT / 'research/experiments/story-native/server3333/src'
        compiler = Path('A:/Coding/MinGW/bin')
        files = [ROOT / 'games/codol/versions/v3_3_3_3/tests/native/story_profile.c',
                 source / 'codol/stats/codol_profile_storage.c',
                 source / 'codol/assets/codol_assets.c']
        files += [source / 'zlib' / name for name in
                  ('inflate.c', 'inffast.c', 'inftrees.c', 'adler32.c', 'crc32.c')]
        includes = (source, source / 'codol/stats', source / 'codol/assets')
        env = dict(os.environ, PATH=str(compiler) + os.pathsep + os.environ['SystemRoot'] + '/System32')
        result = subprocess.run([str(compiler / 'gcc.exe'), '-m32', '-O1', '-std=gnu11',
            '-static-libgcc', *['-I' + str(path) for path in includes],
            *map(str, files), '-o', str(cls.probe)], cwd=cls.root, env=env,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout)

    def test_native_reader_consumes_exported_capture_without_changing_bytes(self):
        store = PrivateProfileStore(self.root / 'lobby', self.root / 'backups')
        store.save(USER_ID, CAPTURE_V19)
        native = self.root / 'profiles'
        store.export_native(USER_ID, native)
        consumed = subprocess.run([str(self.probe), str(native), str(USER_ID)],
                                  check=True, stdout=subprocess.PIPE).stdout
        self.assertEqual(len(consumed), 32768)
        self.assertEqual(hashlib.sha256(consumed).hexdigest(), RAW_V19_SHA256)


if __name__ == '__main__':
    unittest.main()
