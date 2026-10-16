"""The manager starts without any game installation; OS effects are recorded."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManagerStartupTests(unittest.TestCase):
    def launch(self, mode, *flags):
        with tempfile.TemporaryDirectory(prefix='manager startup ') as temporary:
            root = Path(temporary)
            for name in ('Start.ps1', 'tools/check-startup.py', 'scripts/Start-Controller.ps1', 'requirements.txt'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            for name in ('src/controller.py', 'src/manager/installations.py', 'games/codol/versions.json', 'web/dist/index.html'):
                target = root / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_text('test')
            harness = root / 'harness.ps1'
            harness.write_text(r'''
param($Mode,$PythonPath,$Flags)
$global:events=@()
$global:live=$Mode -eq 'existing'
function Get-CimInstance {
    param($ClassName,$Filter)
    if ($global:live) { [pscustomobject]@{ProcessId=101;ParentProcessId=0;Name='python.exe';CommandLine=('python "'+(Join-Path $PSScriptRoot 'src/controller.py')+'"')} }
}
function Get-Process { param($Id) if ($global:live) { [pscustomobject]@{Id=101} } }
function Get-NetTCPConnection {
    param($State)
    if ($global:live -or $Mode -eq 'conflict') { [pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=8765;OwningProcess=$(if($Mode -eq 'conflict'){999}else{101})} }
}
function Get-NetUDPEndpoint {}
function Start-Process {
    param($FilePath,$ArgumentList,$WorkingDirectory,$WindowStyle,$RedirectStandardOutput,$RedirectStandardError,[switch]$PassThru)
    $global:events += $(if ($FilePath -like 'http*') {'browser'} else {'controller'})
    if ($FilePath -notlike 'http*') {
        if ($WindowStyle -ne 'Hidden') { throw 'Controller must start hidden' }
        $global:live=$true
        [pscustomobject]@{Id=101}
    }
}
function Invoke-RestMethod {
    param($Uri,$TimeoutSec,$Method,$ContentType,$Body)
    if ($Uri -like '*/api/game/launch') {$global:events += 'selected-game'; return}
    [pscustomobject]@{profiles=@();game_running=$false;installation=@{state=$(if($Mode -eq 'matched'){'matched'}else{'unselected'})}}
}
function Invoke-WebRequest { param($Uri,$TimeoutSec,[switch]$UseBasicParsing) [pscustomobject]@{StatusCode=200;Content='test'} }
$failure=$null
try {
    $options=@{PythonPath=$PythonPath;StartupTimeoutSeconds=1}
    if($Flags -eq 'check'){$options.CheckOnly=$true}
    if($Flags -eq 'quiet'){$options.NoGame=$true;$options.NoBrowser=$true}
    & (Join-Path $PSScriptRoot 'Start.ps1') @options | Out-Null
} catch {$failure=$_.Exception.Message}
@{events=@($global:events);failure=$failure} | ConvertTo-Json -Compress
''', encoding='utf-8-sig')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                str(harness), mode, sys.executable, flags[0] if flags else 'normal'], capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            return json.loads(result.stdout.decode('utf-8-sig'))

    def test_unselected_opens_manager_without_game_and_selection_uses_control_api(self):
        for mode, events in [('unselected', ['controller', 'browser']), ('matched', ['controller', 'selected-game', 'browser']),
                             ('existing', ['browser'])]:
            with self.subTest(mode=mode):
                result = self.launch(mode)
                self.assertIsNone(result['failure'])
                self.assertEqual(result['events'], events)

    def test_preflight_and_quiet_modes_and_foreign_port(self):
        self.assertEqual(self.launch('unselected', 'check'), {'events': [], 'failure': None})
        self.assertEqual(self.launch('unselected', 'quiet'), {'events': ['controller'], 'failure': None})
        result = self.launch('conflict')
        self.assertEqual(result['events'], [])
        self.assertIn('999', result['failure'])
