"""Session lifecycle at the process/service boundary; never launch the real game."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]


class GameSessionTests(unittest.TestCase):
    def session(self, action, scenario='normal'):
        with tempfile.TemporaryDirectory(prefix='CODOL session ') as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            for name in ('Control-Game.ps1', 'Launch-Game.ps1'):
                shutil.copyfile(ROOT / 'games/codol/versions/v3_3_3_3/scripts' / name, root / 'scripts' / name)
            (root / 'scripts/Control-Services.ps1').write_text("""
param($Action,$PythonPath)
$global:events += "server-$Action"
if ($Scenario -eq 'server-failure' -and $Action -eq 'start') { throw 'Port not ready' }
if ($Scenario -eq 'cleanup-failure' -and $Action -eq 'stop') { throw 'Server still running' }
'{"running":true,"ready":true,"pid":123,"ports":[]}'
""", encoding='utf-8-sig')
            (root / 'scripts/Stop-Game.ps1').write_text("""
$global:events += 'game-stop'
if ($Scenario -ne 'stop-failure') { $global:gameLive = $false }
""", encoding='utf-8-sig')
            harness = root / 'probe.ps1'
            harness.write_text(r'''
param($Action,$Scenario)
$ErrorActionPreference = 'Stop'
$env:CODOL_REPO_ROOT = $PSScriptRoot
$env:CODOL_RUNTIME = Join-Path $PSScriptRoot 'runtime'
$env:CODOL_GAME_ROOT = Join-Path $PSScriptRoot 'game'
$env:CODOL_VERSION_ROOT = $PSScriptRoot
function python.exe {
    $global:LASTEXITCODE=0
    if (($args -join ' ') -like '*background.py*') {
        if (($args -join ' ') -notlike '*-Action watch -GamePid 456*') { throw 'Wrong watcher' }
        $global:events += 'watch-start'
    }
}
$global:events = @()
$global:gameLive = $Action -ne 'start' -and $Scenario -ne 'already-gone'
function Get-Process {
    param($Name,$Id)
    if ($global:gameLive) { [pscustomobject]@{Id=456;ProcessName='codoMP_client_shipRetail';HasExited=$false} | Add-Member -MemberType ScriptMethod -Name WaitForExit -Value { Wait-Process -Id 456 } -PassThru }
}
function Wait-Process {
    param($Id)
    $global:events += 'game-exit'
    $global:gameLive = $Scenario -eq 'replacement'
}
function Start-Process {
    param($FilePath,$ArgumentList,$WorkingDirectory,$Verb,$WindowStyle,[switch]$PassThru)
    if ($Verb -eq 'RunAs') {
        $global:events += 'game-start'
        if ($Scenario -eq 'cancel') { throw 'UAC cancelled' }
        if (($ArgumentList -join ' ') -notlike '*+set dw_username johnClient;set 2822 1;set 3233 1*') { throw 'Wrong game arguments' }
        $global:gameLive = $true
        return [pscustomobject]@{Id=456;HasExited=$false}
    }
    throw 'Unexpected foreground process'
}
$failure = $null
try { & (Join-Path $PSScriptRoot 'scripts\Control-Game.ps1') -Action $Action -GamePid 456 -PythonPath 'python.exe' | Out-Null }
catch { $failure = $_.Exception.Message }
@{events=@($global:events);failure=$failure;running=$global:gameLive} | ConvertTo-Json -Compress
''', encoding='utf-8-sig')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                     str(harness), action, scenario], capture_output=True, timeout=15,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            return json.loads(result.stdout.decode('utf-8-sig'))

    def test_start_waits_for_server_then_launches_game_and_hidden_watcher(self):
        result = self.session('start')
        self.assertIsNone(result['failure'])
        self.assertEqual(result['events'], ['server-start', 'game-start', 'watch-start'])

    def test_failed_start_or_cancel_cleans_server_without_false_success(self):
        for scenario, expected in [('server-failure', ['server-start', 'server-stop']),
                                   ('cancel', ['server-start', 'game-start', 'server-stop'])]:
            with self.subTest(scenario=scenario):
                result = self.session('start', scenario)
                self.assertTrue(result['failure'])
                self.assertEqual(result['events'], expected)

    def test_stop_confirms_game_exit_before_server_and_preserves_server_on_failure(self):
        result = self.session('stop')
        self.assertEqual(result['events'], ['game-stop', 'server-stop'])
        self.assertIsNone(result['failure'])
        failed = self.session('stop', 'stop-failure')
        self.assertTrue(failed['failure'])
        self.assertEqual(failed['events'], ['game-stop'])
        self.assertTrue(self.session('stop', 'cleanup-failure')['failure'])

    def test_natural_exit_stops_server_without_browser_and_does_not_stop_new_session(self):
        result = self.session('watch')
        self.assertEqual(result['events'], ['game-exit', 'server-stop'])
        self.assertIsNone(result['failure'])
        self.assertEqual(self.session('watch', 'replacement')['events'], ['game-exit'])
        self.assertEqual(self.session('watch', 'already-gone')['events'], ['server-stop'])


if __name__ == '__main__':
    unittest.main()
