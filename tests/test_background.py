"""A background server must not keep an HTTP command's output pipes open."""
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BackgroundTests(unittest.TestCase):
    def test_start_services_returns_while_its_child_is_alive(self):
        with tempfile.TemporaryDirectory(prefix='CODOL background ') as directory:
            root = Path(directory)
            server = root / 'games/codol/versions/v3_3_3_3/server/local_server.py'
            server.parent.mkdir(parents=True)
            server.write_text("import sys,time\nprint('ready',flush=True)\nprint('diagnostic',file=sys.stderr,flush=True)\ntime.sleep(30)\n")
            helper = ROOT / 'src/manager/background.py'
            if helper.exists():
                (root / 'src/manager').mkdir(parents=True)
                shutil.copyfile(helper, root / 'src/manager/background.py')
            runtime = root / 'runtime'
            scripts = root / 'scripts'
            scripts.mkdir()
            shutil.copyfile(ROOT / 'games/codol/versions/v3_3_3_3/scripts/Start-Services.ps1', scripts / 'Start-Services.ps1')
            # This test covers detached output pipes; preparation has its own
            # resource/launch tests and must not consume a real game here.
            (scripts / 'Prepare-Resources.ps1').write_text('param($PythonPath,[switch]$RequireServer)\n')
            process = subprocess.Popen(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(scripts / 'Start-Services.ps1'), '-PythonPath', sys.executable],
                env={**os.environ, 'CODOL_REPO_ROOT': str(root), 'CODOL_RUNTIME': str(runtime)},
                creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                output, error = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, error.decode(errors='replace'))
                self.assertIn(b'started', output)
                self.assertEqual((runtime / 'logs/server.stdout.log').read_text().strip(), 'ready')
                self.assertEqual((runtime / 'logs/server.stderr.log').read_text().strip(), 'diagnostic')
            finally:
                pid_file = runtime / 'logs/server.pid'
                if pid_file.exists():
                    os.kill(int(pid_file.read_text(encoding='utf-8-sig')), signal.SIGTERM)
                if process.poll() is None: process.kill()
                process.communicate(timeout=5)
