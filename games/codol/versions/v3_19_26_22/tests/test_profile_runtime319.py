import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ProfileRuntimeTests(unittest.TestCase):
    def test_match_rewards_survive_restart_and_failed_rank_lookup_does_not_partly_pay(self):
        server = Path(__file__).resolve().parents[1] / 'server'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'local-profiles319').mkdir()
            (root / 'profile319.json').write_text('{"name":"Player","experience":90,"rank":1,"other":7}')
            wallet = root / 'local-profiles319/wallet.json'
            wallet.write_text('{"1":2000,"2":7}')
            ranks = root / 'rankTable319.csv'
            ranks.write_text('0,pvt1,0,500,a,a,a,500,,,,,,1\n1,pvt2,500,1200,a,a,a,1700,,,,,,2\n')
            def run(code):
                return subprocess.run([sys.executable, '-B', '-c', code], cwd=server,
                    env={**os.environ, 'CODOL319_SERVER_ROOT': str(root)}, capture_output=True, text=True)
            result = run('import json; from local_profile319 import earn; print(json.dumps([earn(59),earn(120)]))')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [{}, {'1':200,'2':10,'xp':1490,'level':1}])
            result = run('import json; from local_profile319 import wallet,profile_settings; print(json.dumps([wallet(),profile_settings()]))')
            self.assertEqual(json.loads(result.stdout), [{'1':2200,'2':17},
                {'name':'Player','experience':1490,'rank':1,'other':7}])
            profile_before = (root / 'profile319.json').read_bytes()
            before = wallet.read_bytes()
            failed = run('''
import os
from pathlib import Path
from unittest.mock import patch
from local_profile319 import earn
replace = os.replace
def full(source, target):
    if Path(target).name == 'wallet.json':
        raise OSError('disk full')
    replace(source, target)
with patch('os.replace', side_effect=full):
    earn(120)
''')
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn('disk full', failed.stderr)
            self.assertEqual(wallet.read_bytes(), before)
            self.assertEqual((root / 'profile319.json').read_bytes(), profile_before)
            failed = run('from unittest.mock import patch; from local_profile319 import earn; '
                         'p=patch("local_profile319.rank_table",side_effect=ValueError("bad definition")); '
                         'p.start(); earn(120)')
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(wallet.read_bytes(), before)

    def test_current_client_rank_thresholds_do_not_use_supplied_legacy_table(self):
        server = Path(__file__).resolve().parents[1] / 'server'
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-B', '-c',
                'from local_profile319 import level_for; print([level_for(x) for x in (0,1999,2000,3582549,3582550)])'],
                cwd=server, env={**os.environ, 'CODOL319_SERVER_ROOT': directory}, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), [1,1,2,69,70])

    def test_two_instances_read_and_write_only_their_own_profiles(self):
        server = Path(__file__).resolve().parents[1] / 'server'
        with tempfile.TemporaryDirectory() as directory:
            roots = [Path(directory) / name for name in ('First', 'Second')]
            for root in roots:
                root.mkdir()
                (root / 'profile319.json').write_text(json.dumps({'name': root.name}))
                script = ("from local_profile319 import player_name,save_public_info,load_public_info; "
                          "save_public_info(1000001,player_name().encode()); print(load_public_info(1000001).decode())")
                result = subprocess.run([sys.executable, '-B', '-c', script], cwd=server,
                    env={**os.environ, 'CODOL319_SERVER_ROOT': str(root)}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), root.name)
            self.assertEqual((roots[0] / 'local-profiles319/1000001-public.bin').read_bytes(), b'First')
            self.assertEqual((roots[1] / 'local-profiles319/1000001-public.bin').read_bytes(), b'Second')
