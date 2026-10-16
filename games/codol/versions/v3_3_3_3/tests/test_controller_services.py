"""Run the real PowerShell controller script against isolated OS boundaries."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[5]


class ServiceControlTests(unittest.TestCase):
    def probe(self, scenario, action='status'):
        with tempfile.TemporaryDirectory(prefix='CODOL control ') as directory:
            root = Path(directory)
            (root / 'scripts').mkdir()
            (root / 'runtime/logs').mkdir(parents=True)
            (root / 'runtime/logs/server.pid').write_text('999')  # stale foreign PID
            for name in ('Control-Services.ps1', 'Start-Services.ps1'):
                shutil.copyfile(ROOT / 'games/codol/versions/v3_3_3_3/scripts' / name, root / 'scripts' / name)
            harness = root / 'probe.ps1'
            harness.write_text(r'''
param($Scenario, $Action)
$ErrorActionPreference = 'Stop'
$env:CODOL_REPO_ROOT = $PSScriptRoot
$env:CODOL_RUNTIME = Join-Path $PSScriptRoot 'runtime'
$env:CODOL_GAME_ROOT = Join-Path $PSScriptRoot 'game'
$global:source = Join-Path $PSScriptRoot 'games\codol\versions\v3_3_3_3\server\local_server.py'
$global:started = 0
$global:stopped = @()
$global:live = $Scenario -in @('running', 'partial', 'venv', 'duplicate', 'stop-failure', 'missing-match', 'foreign-match', 'other-instance')
function Get-CimInstance {
    param($ClassName, $Filter)
    $items = @([pscustomobject]@{Name='python.exe';ProcessId=999;ParentProcessId=0;CommandLine='python other.py'})
    if ($global:live) {
        $items += [pscustomobject]@{Name='python.exe';ProcessId=101;ParentProcessId=100;CommandLine=('python "'+$global:source+'" --runtime "'+$(if($Scenario -eq 'other-instance'){'C:\another-instance'}else{$env:CODOL_RUNTIME})+'"')}
        if ($Scenario -ne 'missing-match') {
            $items += [pscustomobject]@{Name='codol-match.exe';ProcessId=103;ParentProcessId=$(if ($Scenario -eq 'foreign-match') {999} else {101});CommandLine='codol-match serve';ExecutablePath=(Join-Path $PSScriptRoot 'runtime\builds\codol\v3_3_3_3\rust-match\release\codol-match.exe')}
        }
        if ($Scenario -eq 'venv') { $items += [pscustomobject]@{Name='python.exe';ProcessId=100;ParentProcessId=0;CommandLine=('python "'+$global:source+'" --runtime "'+$(if($Scenario -eq 'other-instance'){'C:\another-instance'}else{$env:CODOL_RUNTIME})+'"')} }
        if ($Scenario -eq 'duplicate') { $items += [pscustomobject]@{Name='python.exe';ProcessId=102;ParentProcessId=0;CommandLine=('python "'+$global:source+'" --runtime "'+$(if($Scenario -eq 'other-instance'){'C:\another-instance'}else{$env:CODOL_RUNTIME})+'"')} }
    }
    # A substring match must never identify another source as this service.
    $items += [pscustomobject]@{Name='python.exe';ProcessId=777;ParentProcessId=0;CommandLine=('python "'+$global:source+'.backup"')}
    if ($Scenario -eq 'editor') { $items += [pscustomobject]@{Name='notepad.exe';ProcessId=888;ParentProcessId=0;CommandLine=('notepad "'+$global:source+'"')} }
    if ($Filter -match 'ProcessId=(\d+)') { return $items | Where-Object ProcessId -eq ([int]$Matches[1]) }
    return $items
}
function Get-NetTCPConnection {
    param($State)
    if ($global:live) { foreach ($port in @(443,3074)) { [pscustomobject]@{LocalPort=$port;LocalAddress='127.0.0.1';OwningProcess=101} } }
    if ($Scenario -eq 'conflict') { [pscustomobject]@{LocalPort=443;LocalAddress='0.0.0.0';OwningProcess=999} }
}
function Get-NetUDPEndpoint {
    if ($global:live -and $Scenario -ne 'partial') { [pscustomobject]@{LocalPort=3074;LocalAddress='127.0.0.1';OwningProcess=101} }
    if ($global:live -and $Scenario -ne 'missing-match') { [pscustomobject]@{LocalPort=28970;LocalAddress='127.0.0.1';OwningProcess=103} }
}
function python.exe {
    if (($args -join ' ') -notlike '*background.py*--runtime*') { throw 'Wrong background command' }
    $global:started++
    $global:live = $Scenario -ne 'exit'
    $global:LASTEXITCODE = 0
    return 101
}
function Stop-Process {
    param($Id,[switch]$Force)
    if ($Id -ne 101) { throw 'Wrong process' }
    $global:stopped += $Id
    if ($Scenario -ne 'stop-failure') { $global:live = $false }
}
try {
    $result = & (Join-Path $PSScriptRoot 'scripts\Control-Services.ps1') -Action $Action -PythonPath 'python.exe'
    $errorText = $null
} catch { $errorText = $_.Exception.Message }
@{state=$(if ($result) { $result | ConvertFrom-Json });error=$errorText;started=$global:started;stopped=@($global:stopped)} | ConvertTo-Json -Depth 8 -Compress
''', encoding='utf-8-sig')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                     str(harness), scenario, action], capture_output=True, timeout=35,
                                    creationflags=subprocess.CREATE_NO_WINDOW)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            return json.loads(result.stdout.decode('utf-8-sig'))

    def test_another_instance_server_is_not_owned_or_stopped(self):
        result = self.probe('other-instance', 'stop')
        self.assertIsNone(result['error'])
        self.assertFalse(result['state']['running'])
        self.assertEqual(result['stopped'], [])

    def test_status_tracks_owned_process_and_each_listener(self):
        for scenario, running, ready in [('stopped', False, False), ('running', True, True),
                                          ('venv', True, True), ('partial', True, False),
                                          ('conflict', False, False)]:
            with self.subTest(scenario=scenario):
                result = self.probe(scenario)
                self.assertIsNone(result['error'])
                self.assertEqual(result['state']['running'], running)
                self.assertEqual(result['state']['ready'], ready)
                self.assertEqual(result['state']['pid'], 101 if running else None)
                self.assertEqual(len(result['state']['ports']), 4)
                self.assertEqual(any(p['conflict'] for p in result['state']['ports']), scenario == 'conflict')
                self.assertEqual(result['started'], 0)
                self.assertEqual(result['stopped'], [])

    def test_start_reuses_owned_process_and_does_not_trust_stale_pid(self):
        for scenario, starts in [('stopped', 1), ('running', 0), ('venv', 0)]:
            with self.subTest(scenario=scenario):
                result = self.probe(scenario, 'start')
                self.assertIsNone(result['error'])
                self.assertTrue(result['state']['ready'])
                self.assertEqual(result['started'], starts)

    def test_conflicts_duplicates_and_early_exit_never_report_started(self):
        for scenario in ('conflict', 'duplicate', 'exit'):
            with self.subTest(scenario=scenario):
                result = self.probe(scenario, 'start')
                self.assertTrue(result['error'])
                self.assertEqual(result['stopped'], [])
                self.assertEqual(result['started'], 1 if scenario == 'exit' else 0)

    def test_stop_only_targets_owned_leaf_even_with_stale_pid(self):
        for scenario, stopped in [('stopped', []), ('running', [101]), ('venv', [101])]:
            with self.subTest(scenario=scenario):
                result = self.probe(scenario, 'stop')
                self.assertIsNone(result['error'])
                self.assertFalse(result['state']['running'])
                self.assertEqual(result['stopped'], stopped)
        self.assertTrue(self.probe('stop-failure', 'stop')['error'])

    def test_open_source_in_editor_is_not_a_server_process(self):
        result = self.probe('editor')
        self.assertFalse(result['state']['running'])
        self.assertEqual(result['stopped'], [])

    def test_match_child_must_be_owned_and_listening_before_ready(self):
        for scenario in ('missing-match','foreign-match'):
            with self.subTest(scenario=scenario):
                result=self.probe(scenario)
                self.assertTrue(result['state']['running'])
                self.assertFalse(result['state']['ready'])
                match=next(p for p in result['state']['ports'] if p['name']=='match')
                self.assertFalse(match['listening'])
                self.assertEqual(match['conflict'],scenario=='foreign-match')


if __name__ == '__main__':
    unittest.main()
