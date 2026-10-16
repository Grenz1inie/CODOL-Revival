"""Directory picker ownership and subprocess result handling."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from manager.folder_picker import choose_folder


class FolderPickerTests(unittest.TestCase):
    def test_selected_unicode_path_and_cancellation(self):
        for path in ['E:\\游戏\\使命召唤', None]:
            output = b'\xef\xbb\xbf' + json.dumps({'path': path}, ensure_ascii=False).encode('utf-8')
            with self.subTest(path=path), patch('manager.folder_picker.subprocess.run',
                    return_value=subprocess.CompletedProcess([], 0, output, b'')):
                self.assertEqual(choose_folder(), path)

    @unittest.skipUnless(sys.platform == 'win32', 'Windows Forms ownership')
    def test_dialog_has_visible_topmost_owner(self):
        with patch('manager.folder_picker.subprocess.run',
                return_value=subprocess.CompletedProcess([], 0, b'{"path":null}', b'')) as run:
            choose_folder()
        command = run.call_args.args[0]
        probe = '''
function Test-DialogOwner($owner) {
    if (!$owner.Visible -or !$owner.IsHandleCreated -or !$owner.TopMost) {
        throw 'Directory dialog owner is not visible and topmost'
    }
    return [Windows.Forms.DialogResult]::Cancel
}
'''
        script = probe + command[-1].replace('$dialog.ShowDialog($owner)', '(Test-DialogOwner $owner)')
        result = subprocess.run([*command[:-1], script], capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
        self.assertIsNone(json.loads(result.stdout.decode('utf-8-sig'))['path'])


if __name__ == '__main__':
    unittest.main()
