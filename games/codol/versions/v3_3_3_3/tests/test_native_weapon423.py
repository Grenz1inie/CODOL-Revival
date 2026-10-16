"""Weapon source ownership and conversion at the existing native asset seam."""
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools'))
sys.path.insert(0, str(ROOT / 'games/codol/versions/v3_3_3_3/tests'))
from build_native_server import STAGE, prepare
from client_reader423 import ClientReader423


class NativeWeapon423Tests(unittest.TestCase):
    def test_current_timing_ammo_and_animation_parameters(self):
        with tempfile.TemporaryDirectory(dir=STAGE) as folder:
            folder = Path(folder)
            source = prepare(folder / 'source')
            output = folder / 'weapon-parameters.exe'
            compiler = Path('A:/Coding/MinGW/bin')
            env = dict(os.environ, PATH=str(compiler)+os.pathsep+os.environ['SystemRoot']+'/System32')
            includes = [source/'src', *[p for p in (source/'src/codol').iterdir() if p.is_dir()]]
            subprocess.run([str(compiler/'gcc.exe'), '-O1', '-std=gnu11', '-static-libgcc',
                '-ffunction-sections', '-fno-asynchronous-unwind-tables', '-Wl,--gc-sections',
                *['-I'+str(p) for p in includes], str(ROOT/'games/codol/versions/v3_3_3_3/tests/native/story_weapon_parameters.c'),
                str(source/'src/codol/weapon/codol_weapon_2697.c'),
                str(source/'src/codol/weapon/codol_weapon_2697_core.c'),
                '-o', str(output)], env=env, check=True, capture_output=True)
            result = subprocess.run([str(output)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('weapon_parameters423 complete=1', result.stdout)
            values = re.search(r'fire=(\d+) delay=(\d+) hold=(\d+)', result.stdout)
            fire, delay, hold = map(int, values.groups())
            client = ClientReader423()
            for hand in (0, 1):
                self.assertEqual(client.weapon_fire_timing(fire=173, delay=137, hold=331, hand=hand),
                                 (fire, delay))
                self.assertEqual(client.weapon_fire_timing(fire=173, delay=137, hold=331,
                                                          grenade=True, hand=hand), (0, hold))

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
                str(ROOT/'games/codol/versions/v3_3_3_3/tests/native/story_weapon_image.c'),
                str(source/'src/codol/weapon/codol_weapon_attachment.c'),
                '-o', str(output)], env=env, check=True, capture_output=True)
            result = subprocess.run([str(output)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertIn('weapon_source_image423 complete=1', result.stdout)
