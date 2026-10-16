"""Integration seam: the rebuilt engine consumes the unchanged current archives."""
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest

import pefile

ROOT = Path(__file__).resolve().parents[5]
STAGE = ROOT / 'research/experiments/story-native'
CLIENT = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'


class NativeAssets423Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = json.loads((STAGE / 'native-build3333.json').read_text())
        cls.executable = Path(manifest['executable'])
        for path, expected in ((ROOT / 'games/codol/versions/v3_3_3_3/reverse/tools/native/server3333.patch', manifest['patch_sha256']),
                               (cls.executable, manifest['executable_sha256'])):
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise AssertionError('Rebuild the current port: python games/codol/versions/v3_3_3_3/reverse/tools/build_native_server.py')

    def run_probe(self, *arguments, options=None):
        env = {key: value for key, value in os.environ.items() if not key.startswith('CODOL_')}
        env['CODOL_ARCHIVE_TRACE'] = '1'
        env.update(options or {})
        return subprocess.run([str(self.executable), *map(str, arguments)], cwd=STAGE,
            env=env, capture_output=True, text=True, errors='backslashreplace', timeout=45,
            creationflags=subprocess.CREATE_NO_WINDOW)

    def test_rebuilt_engine_reconstructs_current_archives(self):
        for name, assets in (('resources-marketplace/2.bin', 8728),
                             ('resources/ff_init_coop_training_mp_cargoship_V29/2.bin', 1174),
                             ('resources-base/ff_init_mp_cargoship_V32/2.bin', 338)):
            with self.subTest(archive=name):
                result = self.run_probe('--codol-archive-probe', STAGE / name, CLIENT)
                self.assertEqual(result.returncode, 0, result.stdout[-1800:]+result.stderr[-1800:])
                self.assertIn(f'assets={assets} ', result.stdout)
                self.assertIn('reference_replay ok=1', result.stdout)

    def test_rebuilt_engine_resolves_current_world_dependencies(self):
        archives = [STAGE / name for name in ('resources-common-gfx/2.bin',
            'resources-common-gfx/5.bin', 'resources-common/ff_init_common_mp_V43/5.bin',
            'resources-base/ff_init_mp_cargoship_V32/2.bin',
            'resources/ff_init_coop_training_mp_cargoship_V29/2.bin')]
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship', *archives)
        self.assertEqual(result.returncode, 0, result.stdout[-2600:]+result.stderr[-1600:])
        self.assertIn('instances=9173 unresolved=0', result.stdout)
        self.assertIn('model_calls=9173 failures=0', result.stdout)
        self.assertIn('dynamic_models=246 effects=8 presets=246 trigger_models=64', result.stdout)
        self.assertIn('runtime_complete ok=1', result.stdout)
        self.assertIn('published=0 physics_activated=0', result.stdout)
        self.assertIn('engine_started=0 network_started=0', result.stdout)

    def test_rebuilt_engine_rejects_truncated_or_unsupported_archive(self):
        source = (STAGE / 'resources/ff_init_coop_training_mp_cargoship_V29/2.bin').read_bytes()
        with tempfile.TemporaryDirectory(dir=STAGE) as folder:
            path = Path(folder) / 'invalid.ff'
            for data in (source[:64], source[:8]+b'\x00\x00\x00\x00'+source[12:]):
                path.write_bytes(data)
                result = self.run_probe('--codol-archive-probe', path, CLIENT)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('archive_failure', result.stdout)
                self.assertNotIn('reference_replay ok=1', result.stdout)

    def test_current_weapon_dependencies_preserve_all_animation_slots(self):
        archives = [STAGE / name for name in ('resources-common-gfx/2.bin',
            'resources-common-gfx/5.bin', 'resources-common/ff_init_common_mp_V43/5.bin',
            'resources-base/ff_init_mp_cargoship_V32/2.bin',
            'resources/ff_init_coop_training_mp_cargoship_V29/2.bin')]
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship', *archives,
            options={'CODOL_WEAPON_PROBE': '1', 'CODOL_WEAPON_SOURCE_ONLY': '1'})
        for name in ('ak104_mp', 'deserteagle_mp', 'white_phosphorus_grenade_mp', 'flash_grenade_mp'):
            self.assertIn(f'runtime_weapon name={name} source=1 animations=1 effects=1 '
                'sounds=1 visuals=1 ammo=1 tail=1 tags=1 slots=168', result.stdout)
            self.assertIn(f'runtime_weapon_image name={name} ready=1 animations=168 effects=35 visuals=18',result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout[-2600:]+result.stderr[-1600:])
        self.assertIn('runtime_complete ok=1', result.stdout)
        self.assertIn('engine_started=0 network_started=0', result.stdout)

    def test_current_map_entities_and_glass_are_available_to_native_world(self):
        archives = [STAGE / name for name in ('resources-common-gfx/2.bin',
            'resources-common-gfx/5.bin', 'resources-common/ff_init_common_mp_V43/5.bin',
            'resources-base/ff_init_mp_cargoship_V32/2.bin',
            'resources/ff_init_coop_training_mp_cargoship_V29/2.bin')]
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship', *archives,
            options={'CODOL_MAP_STATE_PROBE': 'coop_training_mp_cargoship','CODOL_REGISTRY_PROBE':'1'})
        self.assertIn('runtime_registry complete=1 weapons=297 engine_registered=0',result.stdout)
        self.assertRegex(result.stdout, r'runtime_map_state addon=1 bytes=174339 triggers=142 glass=1 pieces=12')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:]+result.stderr[-1200:])

    def test_current_weapon_core_resolves_real_dependencies(self):
        archives = [STAGE / 'startup-assets/chinese' / (name+'.ff') for name in (
            'code_pre_gfx_mp', 'localized_code_pre_gfx_mp', 'code_post_gfx_default_mp',
            'code_post_gfx_mp', 'localized_code_post_gfx_mp', 'common_mp', 'localized_common_mp',
            'common_marketplace_lite', 'localized_common_marketplace_lite',
            'common_gametype_coop', 'localized_common_gametype_coop',
            'mp_cargoship', 'coop_training_mp_cargoship')]
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship', *archives,
            options={'CODOL_WEAPON_PROBE': '1', 'CODOL_WEAPON_CORE_ONLY': '1',
                     'CODOL_MODEL_ROOT': str(STAGE/'startup-assets/main/models')})
        evidence = ROOT / 'research/evidence/server3333-weapon-core-assets.log'
        evidence.write_text(result.stdout+result.stderr)
        self.assertEqual(result.returncode, 0, result.stdout[-4000:]+result.stderr[-1200:])
        for name in ('none', 'defaultweapon_mp'):
            self.assertIn(f'runtime_target_weapon_core name={name} variant=stock constructed=1', result.stdout)
            self.assertIn(f'runtime_target_core_lifecycle name={name} variant=stock early_rollback=1 '
                          'late_rollback=1 replacement=1 owned_sound_pointer=1', result.stdout)
        self.assertIn('runtime_minimal_cache count=2 reuse=1 retired=1 rejected=1', result.stdout)
        self.assertIn('engine_started=0 network_started=0', result.stdout)

    def test_current_animation_script_loads_definitions_before_main(self):
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship',
            STAGE/'startup-assets/chinese/code_post_gfx_default_mp.ff',
            STAGE/'startup-assets/chinese/code_post_gfx_mp.ff',
            STAGE/'startup-assets/chinese/common_mp.ff',
            STAGE/'startup-assets/chinese/mp_cargoship.ff',
            STAGE/'startup-assets/chinese/coop_training_mp_cargoship.ff',
            options={'CODOL_ANIMATION_TEXT_PROBE':'1'})
        self.assertEqual(result.returncode, 0, result.stdout[-2000:]+result.stderr[-1200:])
        self.assertIn('runtime_animation_text definitions_first=1 owned_copy=1 missing_rejected=1', result.stdout)

    def test_current_animation_tokens_have_native_lookup_and_event_storage(self):
        data = CLIENT.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
            'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b')
        pe = pefile.PE(data=data, fast_load=True)
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship',
            STAGE/'startup-assets/chinese/code_post_gfx_default_mp.ff',
            STAGE/'startup-assets/chinese/code_post_gfx_mp.ff',
            STAGE/'startup-assets/chinese/common_mp.ff',
            STAGE/'startup-assets/chinese/mp_cargoship.ff',
            STAGE/'startup-assets/chinese/coop_training_mp_cargoship.ff',
            options={'CODOL_ANIMATION_TEXT_PROBE':'1'})
        self.assertEqual(result.returncode, 0, result.stdout[-2000:]+result.stderr[-1200:])
        for kind, address, count in (('event', 0xce4a20, 33), ('perk', 0xce4c18, 5)):
            entries = {name.lower(): index for name, index in re.findall(
                rf'runtime_animation_token kind={kind} name=(.+) index=(\d+)', result.stdout)}
            for index in range(count):
                pointer, = struct.unpack('<I', pe.get_data(address-pe.OPTIONAL_HEADER.ImageBase+8*index, 4))
                name = pe.get_string_at_rva(pointer-pe.OPTIONAL_HEADER.ImageBase).decode().lower()
                with self.subTest(kind=kind, token=name):
                    self.assertIn(name, entries)
            if kind == 'event':
                self.assertEqual(list(map(int, entries.values())), list(range(count)))
            else:
                self.assertEqual(entries['grenadedeath'], '2')
                self.assertEqual(entries['laststand'], '1')
        self.assertIn('runtime_animation_tokens lookup=1 casefold=1 missing_rejected=1 event_bounds=1', result.stdout)

    def test_missing_animation_keeps_its_name_without_mutating_void(self):
        result = self.run_probe('--codol-runtime-probe', CLIENT, 'mp_cargoship',
            STAGE/'startup-assets/chinese/code_post_gfx_default_mp.ff',
            STAGE/'startup-assets/chinese/code_post_gfx_mp.ff',
            STAGE/'startup-assets/chinese/common_mp.ff',
            STAGE/'startup-assets/chinese/mp_cargoship.ff',
            STAGE/'startup-assets/chinese/coop_training_mp_cargoship.ff',
            options={'CODOL_DEFAULT_XANIM_PROBE':'1'})
        self.assertEqual(result.returncode, 0, result.stdout[-2200:]+result.stderr[-1200:])
        self.assertIn('runtime_default_xanim named=1 cached=1 distinct=1 source_unchanged=1', result.stdout)
