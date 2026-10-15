"""Weapon source ownership and conversion at the existing native asset seam."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_native_server import STAGE, prepare


class NativeWeapon423Tests(unittest.TestCase):
    def test_owned_source_retains_new_dependencies_and_rejects_graph_growth(self):
        with tempfile.TemporaryDirectory(dir=STAGE) as folder:
            folder = Path(folder)
            source = prepare(folder / 'source')
            output = folder / 'weapon-image.exe'
            compiler = Path('A:/Coding/mingw64/bin')
            env = dict(os.environ, PATH=str(compiler)+os.pathsep+os.environ['SystemRoot']+'/System32')
            subprocess.run([str(compiler/'gcc.exe'), '-O1', '-std=gnu11', '-static-libgcc',
                '-ffunction-sections', '-fno-asynchronous-unwind-tables', '-Wl,--gc-sections',
                '-I'+str(source/'src/codol/assets'), '-I'+str(source/'src/codol/weapon'),
                str(ROOT/'tests/native/story_weapon_image.c'),
                str(source/'src/codol/weapon/codol_weapon_attachment.c'),
                '-o', str(output)], env=env, check=True, capture_output=True)
            result = subprocess.run([str(output)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('weapon_source_image423 complete=1', result.stdout)
