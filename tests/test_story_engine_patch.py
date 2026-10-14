"""Experimental PE output boundary; offsets independently recovered with REA."""
import importlib.util
from pathlib import Path
import unittest
import json
import os
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


class StoryEnginePatchTests(unittest.TestCase):
    def test_archive_probe_reads_current_version_before_resource_replay(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'tools/story_engine_patch.py')
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
                                  cwd=folder, env=env, capture_output=True, text=True, timeout=30)
            self.assertIn('archive_open size=21583990 assets=1174 strings=624', task.stdout,
                          f'{task.returncode}: {task.stdout} {task.stderr}')
            # Replay is a separate compatibility step; its failure must remain visible.
            self.assertIn('reference_replay', task.stdout)
            # ReplayZone discards its output context on a later model failure.
            # Therefore the subsequent ReadNetConst output cannot prove NCS replay.
            match = re.search(r'reference_replay ok=(\d) failed_index=(\d+)', task.stdout)
            self.assertIsNotNone(match)
            # Asset 13 is the first model with an inline 3.3.3.3 material.
            self.assertTrue(match[1] == '1' or int(match[2]) >= 27, task.stdout[:300])
            manifest = json.loads((stage / 'resources-base/manifest.json').read_text())
            file = next(f for a in manifest['archives'] for f in a['files']
                        if f['name'].endswith('/mp_cargoship.ff'))
            task = subprocess.run([str(executable), '--codol-archive-probe', str(ROOT / file['file']), str(client)],
                                  cwd=folder, env=env, capture_output=True, text=True, timeout=30)
            self.assertIn('archive_open size=87492551 assets=338 strings=367', task.stdout)
            match = re.search(r'reference_replay ok=(\d) failed_index=(\d+)', task.stdout)
            self.assertIsNotNone(match)
            # Asset 201 is the base world's full geometry, after its effects.
            self.assertTrue(match[1] == '1' or int(match[2]) >= 202, task.stdout[:300])

    def test_unverified_or_already_patched_images_are_rejected(self):
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'tools/story_engine_patch.py')
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
        spec = importlib.util.spec_from_file_location('story_engine_patch', ROOT / 'tools/story_engine_patch.py')
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
