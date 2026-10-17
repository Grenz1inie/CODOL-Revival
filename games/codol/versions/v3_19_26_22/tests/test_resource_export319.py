import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from games.codol.versions.v3_19_26_22.client import resource_export


class ResourceExportTests(unittest.TestCase):
    def test_generated_catalog_uses_client_ids_and_never_imports_player_state(self):
        loaded = Mock()
        loaded.weapons.return_value = ['none', 'm4_mp']
        loaded.classes.return_value = {'classes': [{'primary': 12}], 'loadoutVersion': 20}
        loaded.table.return_value = [['0', 'pvt', '0', '500']]
        registry = {'items': [(10001,7,'m4_mp'),(20001,8,'sto_m4')],
                    'weapons': [(10001,'m4_mp',1,[20001]+[0]*14)], 'parts': [(6,'sto_m4')],
                    'skus': [(5,3,[10001],1,400,0)]}
        result = resource_export.common_files(loaded,registry)
        self.assertEqual(json.loads(result['item-registry319.json'])['items'],[[10001,'m4_mp'],[20001,'sto_m4']])
        self.assertIn(b'10001 7 m4_mp\n',result['item-ids319.txt'])
        self.assertEqual(result['sku-items319.txt'],b'5 3 10001\n')
        self.assertEqual(result['sku-prices319.txt'],b'5 1 400 0\n')
        self.assertIn(b'part 6 sto_m4\n',result['weapon-parts319.txt'])
        self.assertIn(b'item 10001 m4_mp 1 20001 ',result['weapon-parts319.txt'])
        self.assertFalse(any('profile' in p or 'wallet' in p or p.endswith('.exe') for p in result))

    def test_publication_marks_readiness_last_and_preserves_progress(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'profile319.json').write_bytes(b'current player')
            with self.assertRaisesRegex(TimeoutError,'resources'):
                resource_export.wait_ready(root,timeout=0)
            resource_export.publish(root,{'item-ids319.txt':b'new ids'}, {'pid':123,'created':45})
            resource_export.wait_ready(root,timeout=0)
            marker=json.loads((root/'common-ready.json').read_text())
            self.assertEqual(marker['game'],{'pid':123,'created':45})
            self.assertEqual(marker['outputs']['item-ids319.txt'],hashlib.sha256(b'new ids').hexdigest())
            self.assertEqual((root/'profile319.json').read_bytes(),b'current player')
            (root/'item-ids319.txt').write_bytes(b'corrupt')
            with self.assertRaisesRegex(ValueError,'item-ids319'):
                resource_export.validate_common(root)

    def test_map_capture_publishes_ladders_and_clipmap_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'clipmap.bin';exe=root/'game.exe';identity={'pid':1,'created':2}
            with patch.object(resource_export,'ReadOnlyProcess') as process, \
                    patch.object(resource_export,'LoadedResources') as loaded:
                loaded.return_value.clipmap.side_effect=ValueError('map is not loaded')
                with self.assertRaisesRegex(ValueError,'not loaded'):
                    resource_export.export_map(target,identity,exe,'mp_seatown')
                self.assertFalse(target.exists())
                loaded.return_value.clipmap.side_effect=None
                loaded.return_value.clipmap.return_value=(b'CM319', [{'mins':[1,2,3],'maxs':[4,5,6]}])
                resource_export.export_map(target,identity,exe,'mp_seatown')
                self.assertEqual(target.read_bytes(),b'CM319')
                self.assertEqual(json.loads(target.with_suffix('.ladders.json').read_text())[0]['mins'],[1,2,3])
                process.assert_called_with(identity,exe)

    def test_read_only_process_rejects_stale_identity_before_any_memory_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/'game.exe';exe.write_bytes(b'verified executable')
            api=Mock();api.OpenProcess.return_value=101
            api.QueryFullProcessImageNameW.side_effect=lambda handle,flag,buffer,size: setattr(buffer,'value',str(exe)) or True
            api.GetProcessTimes.return_value=True  # zero FILETIME, not the requested process creation time
            with patch.object(resource_export.ctypes,'WinDLL',return_value=api), \
                    patch.object(resource_export,'CLIENT_SHA256',hashlib.sha256(exe.read_bytes()).hexdigest()):
                with self.assertRaisesRegex(ValueError,'identity'):
                    resource_export.ReadOnlyProcess({'pid':77,'created':123},exe)
            api.OpenProcess.assert_called_once_with(0x410,False,77)
            api.ReadProcessMemory.assert_not_called()
            api.CloseHandle.assert_called_once_with(101)
