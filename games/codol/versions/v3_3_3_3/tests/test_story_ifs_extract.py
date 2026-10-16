"""Read-only extraction against the installed first-map archive, not mock bytes."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]
GAME = ROOT.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z'
EXPERIMENT = ROOT / 'research/experiments/story-native'


class StoryIfsExtractTests(unittest.TestCase):
    def test_first_map_extracts_list_and_two_fastfiles_without_changing_input(self):
        source = GAME / 'IIPS/IIPSDownload/ff_init_coop_training_mp_cargoship_V29.ifs'
        expected_list = (b'ff_init_coop_training_mp_cargoship.lst\r\n'
                         b'client_shipRetail/chinese/coop_training_mp_cargoship.ff\r\n'
                         b'client_shipRetail/chinese/coop_training_mp_cargoship_load.ff\r\n')
        before = hashlib.sha256(source.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(dir=EXPERIMENT) as folder:
            folder = Path(folder)
            archive = folder / source.name
            shutil.copyfile(source, archive)
            listing = subprocess.run([str(EXPERIMENT / 'ifs-read.exe'),
                                      str(GAME / 'IIPS/IFS2.dll'), str(archive), '--list'],
                                     capture_output=True, text=True, timeout=30)
            self.assertEqual(listing.returncode, 0, listing.stderr)
            self.assertEqual(list(folder.iterdir()), [archive])
            result = subprocess.run([str(EXPERIMENT / 'ifs-read.exe'),
                                     str(GAME / 'IIPS/IFS2.dll'), str(archive), str(folder)],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(listing.stdout, result.stdout)
            rows = [line.split('\t', 2) for line in result.stdout.splitlines()]
            self.assertEqual(len(rows), 3)
            contents = {name.lower().replace('\\', '/'): (folder / (index + '.bin')).read_bytes()
                        for index, size, name in rows}
            self.assertEqual(contents['ff_init_coop_training_mp_cargoship.lst'], expected_list)
            for name, data in contents.items():
                if name.endswith('.ff'):
                    self.assertEqual(data[:12], b'IWff0100\xa7\x01\0\0')
            for index, size, name in rows:
                self.assertEqual(len(contents[name.lower().replace('\\', '/')]), int(size))
            self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), before)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), before)


if __name__ == '__main__':
    unittest.main()
