"""Experimental PE output boundary; offsets independently recovered with REA."""
import importlib.util
from pathlib import Path
import unittest
import json
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[5]


class StoryEnginePatchTests(unittest.TestCase):
    def test_marketplace_images_resolve_shared_aliases(self):
        # Ordinary 2697 startup was withdrawn after the user's static-reference
        # correction. Its asset-506 failure is retained in startup-r3tv5a84;
        # reproduce the same defect through the no-engine archive consumer.
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stage = ROOT / 'research/experiments/story-native'
        original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
        client = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        with tempfile.TemporaryDirectory(dir=stage) as folder:
            executable = Path(folder) / 'archive423.exe'
            executable.write_bytes(module.patch_archive427(original))
            task = subprocess.run([str(executable), '--codol-archive-probe',
                                   str(stage / 'resources-marketplace/2.bin'), str(client)],
                                  cwd=folder, capture_output=True, text=True,
                                  errors='backslashreplace', timeout=30,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertIn('archive_open size=19936745 assets=8728 strings=686', task.stdout)
            self.assertIn('reference_replay ok=1', task.stdout, task.stdout[:2000] + task.stderr[-1000:])
            self.assertEqual(task.returncode, 0, task.stdout[-1000:] + task.stderr[-1000:])

    def test_world_probe_resolves_static_model_materials(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        stage = ROOT / 'research/experiments/story-native'
        manifest = json.loads((stage / 'resources-base/manifest.json').read_text())
        file = next(f for a in manifest['archives'] for f in a['files']
                    if f['name'].endswith('/mp_cargoship.ff'))
        client = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
        # The base map references models/materials defined by these shared zones.
        archives = [stage / 'resources-common-gfx/2.bin',
                    stage / 'resources-common-gfx/5.bin',
                    stage / 'resources-common/ff_init_common_mp_V43/5.bin',
                    ROOT / file['file'],
                    stage / 'resources/ff_init_coop_training_mp_cargoship_V29/2.bin']
        with tempfile.TemporaryDirectory(dir=stage) as folder:
            executable = Path(folder) / 'dedrun-world423.exe'
            executable.write_bytes(module.patch_archive427(original))
            env = {key: value for key, value in os.environ.items() if not key.startswith('CODOL_')}
            env['CODOL_ARCHIVE_TRACE'] = '1'
            task = subprocess.run([str(executable), '--codol-runtime-probe', str(client),
                                   'mp_cargoship', *map(str, archives)], cwd=folder, env=env,
                                  capture_output=True, text=True, errors='backslashreplace', timeout=45,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            summary = '\n'.join(line for line in task.stdout.splitlines()
                                if line.startswith(('runtime_mount', 'runtime_map', 'runtime_complete')))
            self.assertIn('runtime_mount ok=1', summary, summary + '\n' + task.stderr[-1500:])
            self.assertIn('instances=9173 unresolved=0 model_calls=9173 failures=0', summary,
                          summary + '\n' + task.stderr[-1000:])
            self.assertIn('runtime_collision native=1 ', task.stdout)
            self.assertIn('runtime_dynamic decoded=1 category0=246 category1=0', task.stdout,
                          task.stdout[-2000:] + task.stderr[-1000:])
            self.assertIn('runtime_clipmap native=1 ', task.stdout, task.stdout[-3000:])
            self.assertIn('runtime_story_addon ok=1 text_bytes=174339 triggers=142 hulls=169 slabs=62',
                          task.stdout, task.stdout[-3000:])
            self.assertIn('runtime_complete ok=1 ', summary, task.stdout[-3000:])
            self.assertEqual(task.returncode, 0, task.stderr[-1000:])

    def test_archive_probe_reads_current_version_before_resource_replay(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
        stage = ROOT / 'research/experiments/story-native'
        manifest = json.loads((stage / 'resources/manifest.json').read_text())
        file = next(f for a in manifest['archives'] for f in a['files']
                    if f['name'].endswith('/coop_training_mp_cargoship.ff'))
        client = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
        with tempfile.TemporaryDirectory(dir=stage) as folder:
            executable = Path(folder) / 'dedrun-archive427.exe'
            executable.write_bytes(module.patch_archive427(original))
            env = {key: value for key, value in os.environ.items() if not key.startswith('CODOL_')}
            task = subprocess.run([str(executable), '--codol-archive-probe', str(ROOT / file['file']), str(client)],
                                  cwd=folder, env=env, capture_output=True, text=True,
                                  errors='backslashreplace', timeout=30)
            self.assertIn('archive_open size=21583990 assets=1174 strings=624', task.stdout,
                          f'{task.returncode}: {task.stdout} {task.stderr}')
            # Replay is a separate compatibility step; its failure must remain visible.
            self.assertIn('reference_replay', task.stdout)
            # ReplayZone discards its output context on a later model failure.
            # Therefore the subsequent ReadNetConst output cannot prove NCS replay.
            match = re.search(r'reference_replay ok=(\d) failed_index=(\d+)', task.stdout)
            self.assertIsNotNone(match)
            self.assertEqual(match[1], '1', task.stdout[:300])
            self.assertEqual(task.stdout.count('netconst valid=1'), 12, task.stdout[:500])
            self.assertIn('model_conversion ok=1', task.stdout,
                          'Shared model skeletons must relocate, not only consume source bytes')
            manifest = json.loads((stage / 'resources-base/manifest.json').read_text())
            file = next(f for a in manifest['archives'] for f in a['files']
                        if f['name'].endswith('/mp_cargoship.ff'))
            task = subprocess.run([str(executable), '--codol-archive-probe', str(ROOT / file['file']), str(client)],
                                  cwd=folder, env=env, capture_output=True, text=True,
                                  errors='backslashreplace', timeout=30)
            self.assertIn('archive_open size=87492551 assets=338 strings=367', task.stdout)
            match = re.search(r'reference_replay ok=(\d) failed_index=(\d+)', task.stdout)
            self.assertIsNotNone(match)
            self.assertEqual(match[1], '1', task.stdout[:300])
            self.assertIn('collision_conversion map=mp_cargoship status=1 ', task.stdout)

    def test_unverified_or_already_patched_images_are_rejected(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
        altered = bytearray(original)
        altered[-1] ^= 1
        for image in (bytes(altered), original[:-1], module.patch_configstrings(original)):
            with self.subTest(length=len(image)), self.assertRaisesRegex(ValueError, 'hash'):
                module.patch_configstrings(image)
            with self.subTest(archive_length=len(image)), self.assertRaisesRegex(ValueError, 'hash'):
                module.patch_archive427(image)

    def test_configstring_alias_count_matches_current_client_without_other_changes(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/story_engine_patch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = (ROOT / 'research/references/codol2697/codol_dedrun.exe.bin').read_bytes()
        patched = module.patch_configstrings(original)
        # REA: writer count immediate 11 -> 10; admitted count 2047 -> 1023.
        self.assertEqual(patched[0x9fc4d:0x9fc55], bytes.fromhex('c7 44 24 08 0a 00 00 00'))
        self.assertEqual(patched[0x9f8b4:0x9f8bb], bytes.fromhex('81 7d 1c ff 03 00 00'))
        self.assertEqual(len(patched), len(original))
        self.assertEqual([i for i, pair in enumerate(zip(original, patched)) if pair[0] != pair[1]],
                         [0x9f8b8, 0x9fc51])


if __name__ == '__main__':
    unittest.main()
