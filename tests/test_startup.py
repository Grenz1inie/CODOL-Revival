"""Startup preflight uses disposable files, never the player's runtime or game."""
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('check_startup', ROOT / 'tools/check-startup.py')
startup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(startup)


class StartupFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='codol startup ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'CODOL Revival 测试'
        self.game = self.root.parent / 'CODOL_Experience_V3.3.3.3_FULL.7z'
        for name in ('src/local_server.py', 'src/controller.py', 'scripts/Start-Services.ps1',
                     'scripts/Start-Controller.ps1', 'scripts/Launch-Game.ps1',
                     'scripts/Control-Game.ps1', 'scripts/Control-Services.ps1', 'scripts/Stop-Game.ps1',
                     'data/marketplace-catalog.json', 'web/dist/index.html'):
            self.write(self.root / name, '{}')
        self.write(self.root / 'web/dist/index.html',
                   '<script src="/assets/app.js"></script><link rel="stylesheet" href="/assets/app.css">')
        self.write(self.root / 'web/dist/assets/app.js', '// test')
        self.write(self.root / 'web/dist/assets/app.css', 'body{}')
        self.write(self.root / 'requirements.txt', (ROOT / 'requirements.txt').read_text())
        self.write(self.game / 'codoMP_client_shipRetail.exe', 'test executable; never started')
        self.write(self.game / 'dwauth.ini', '127.0.0.1 3074\n127.0.0.1 443\n0x03EA\n')
        self.write(self.game / 'stun.ini', '127.0.0.1\n')
        self.make_certificate()

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def make_certificate(self, expired=False):
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
        now = datetime.now(timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - timedelta(days=2))
                .not_valid_after(now + timedelta(days=-1 if expired else 2))
                .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
                .sign(key, hashes.SHA256()))
        pem = cert.public_bytes(serialization.Encoding.PEM).decode()
        for path in (self.root / 'runtime/certs/ca.pem', self.root / 'runtime/certs/server.pem',
                     self.game / 'cacert.pem'):
            self.write(path, pem)
        self.write(self.root / 'runtime/certs/server-key.pem', key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()).decode())


class StartupChecksTests(StartupFixture, unittest.TestCase):
    def test_valid_environment_is_read_only_and_needs_no_node_when_ui_is_built(self):
        before = {p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()}
        self.assertEqual(startup.check_environment(self.root), [])
        self.assertEqual({p: p.read_bytes() for p in self.root.parent.rglob('*') if p.is_file()}, before)

    def test_missing_files_are_reported_together_with_frontend_build_instructions(self):
        for name in ('src/local_server.py', 'web/dist/index.html', 'runtime/certs/server.pem',
                     'scripts/Control-Game.ps1', 'scripts/Control-Services.ps1', 'scripts/Stop-Game.ps1'):
            (self.root / name).unlink()
        errors = '\n'.join(startup.check_environment(self.root))
        for expected in ('local_server.py', 'server.pem', 'npm ci', 'npm run build',
                         'Control-Game.ps1', 'Control-Services.ps1', 'Stop-Game.ps1'):
            self.assertIn(expected, errors)

    def test_incomplete_frontend_assets_are_rejected(self):
        (self.root / 'web/dist/assets/app.js').unlink()
        self.assertIn('app.js', '\n'.join(startup.check_environment(self.root)))

    def test_python_and_dependency_failures_include_repair_commands(self):
        with patch.object(sys, 'version_info', (3, 8, 0)):
            self.assertIn('Python', '\n'.join(startup.check_environment(self.root)))
        with patch.object(startup.metadata, 'version', return_value='0.0'):
            self.assertIn('pip install -r', '\n'.join(startup.check_environment(self.root)))
        with patch.object(startup.metadata, 'version', side_effect=startup.metadata.PackageNotFoundError):
            self.assertIn('cryptography', '\n'.join(startup.check_environment(self.root)))

    def test_wrong_game_endpoints_and_settings_are_rejected_without_repairing_files(self):
        self.write(self.game / 'dwauth.ini', 'example.com 3074\n127.0.0.1 443\n0x03EA')
        self.write(self.game / 'stun.ini', 'example.com')
        self.write(self.root / 'runtime/data/controller.json', '{"skip_tutorial":"false"}')
        errors = '\n'.join(startup.check_environment(self.root))
        for name in ('dwauth.ini', 'stun.ini', 'skip_tutorial'):
            self.assertIn(name, errors)
        self.assertEqual((self.game / 'stun.ini').read_text(), 'example.com')

    def test_expired_invalid_or_untrusted_certificates_are_rejected(self):
        self.make_certificate(expired=True)
        self.assertIn('expired', '\n'.join(startup.check_environment(self.root)))
        self.make_certificate()
        self.write(self.game / 'cacert.pem', '')
        self.assertIn('cacert.pem', '\n'.join(startup.check_environment(self.root)))
        self.write(self.root / 'runtime/certs/server-key.pem', 'invalid key')
        self.assertIn('certificate', '\n'.join(startup.check_environment(self.root)))

    def test_server_signed_by_another_ca_returns_an_actionable_failure(self):
        original_server = (self.root / 'runtime/certs/server.pem').read_bytes()
        self.make_certificate()
        (self.root / 'runtime/certs/server.pem').write_bytes(original_server)
        self.assertIn('certificate', '\n'.join(startup.check_environment(self.root)))


@unittest.skipUnless(os.name == 'nt', 'Windows PowerShell launcher')
class LauncherTests(StartupFixture, unittest.TestCase):
    def setUp(self):
        super().setUp()
        for name in ('Start.ps1', 'tools/check-startup.py', 'scripts/Start-Services.ps1',
                     'scripts/Start-Controller.ps1', 'scripts/Launch-Game.ps1',
                     'scripts/Control-Game.ps1', 'scripts/Control-Services.ps1'):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)

    def run_launcher(self, *flags, mode='normal', repeat=False, python_path=sys.executable):
        # Only OS process/network/browser boundaries are replaced. Run the real
        # entry point, child scripts and Python checks in a disposable layout.
        literal = lambda value: "'" + str(value).replace("'", "''") + "'"
        harness = self.root / 'harness.ps1'
        harness.write_text(r'''
$ErrorActionPreference = 'Stop'
$global:launchEvents = @()
$global:fixtureProcesses = @()
$global:fixtureRoot = $PSScriptRoot
$global:fixtureMode = MODE
function Add-FixtureProcess($source, $processId) {
    $proc = [pscustomobject]@{ Id=$processId; ProcessId=$processId; ParentProcessId=0; Name='python.exe';
        CommandLine=('python.exe "' + (Join-Path $global:fixtureRoot $source) + '"') }
    $global:fixtureProcesses += $proc
    return $proc
}
if ($global:fixtureMode -eq 'existing') {
    Add-FixtureProcess 'src\local_server.py' 41001 | Out-Null
    Add-FixtureProcess 'src\controller.py' 41002 | Out-Null
}
function Get-CimInstance {
    param($ClassName, $Filter)
    if ($Filter -match '^ProcessId=(\d+)$') {
        return $global:fixtureProcesses | Where-Object ProcessId -eq ([int]$Matches[1])
    }
    return $global:fixtureProcesses
}
function Get-Process {
    param($Name, $Id)
    if ($Name -eq 'codoMP_client_shipRetail') {
        return $global:fixtureProcesses | Where-Object Name -eq 'codoMP_client_shipRetail.exe'
    }
    return $global:fixtureProcesses | Where-Object Id -eq $Id
}
function Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle,
          $RedirectStandardOutput, $RedirectStandardError, $Verb, [switch]$PassThru)
    $global:launchEvents += [pscustomobject]@{file=$FilePath; arguments=@($ArgumentList); window=$WindowStyle; verb=$Verb}
    if ($FilePath -like 'http*' -or ($ArgumentList -join ' ') -like '*-Action watch*') { return }
    if ($Verb -eq 'RunAs') {
        if ($global:fixtureMode -eq 'cancel') { throw 'UAC cancelled' }
        $proc = [pscustomobject]@{Id=41003; ProcessId=41003; Name='codoMP_client_shipRetail.exe'; CommandLine=$FilePath}
        $global:fixtureProcesses += $proc
        return $proc
    }
    $source = 'src\controller.py'
    $processId = 41002
    if (($ArgumentList -join ' ') -like '*local_server.py*') { $source = 'src\local_server.py'; $processId = 41001 }
    $proc = Add-FixtureProcess $source $processId
    if ($global:fixtureMode -eq 'venv') {
        $parent = Add-FixtureProcess $source ($processId + 10)
        $proc.ParentProcessId = $parent.ProcessId
        return $parent
    }
    if ($processId -eq 41001) {
        if ($global:fixtureMode -eq 'crash') { $global:fixtureProcesses = @() }
    }
    return $proc
}
function Stop-Process {
    param($Id,[switch]$Force)
    $global:fixtureProcesses = @($global:fixtureProcesses | Where-Object ProcessId -ne $Id)
}
function Get-NetTCPConnection {
    param($State)
    foreach ($proc in $global:fixtureProcesses) {
        $ports = @()
        if ($proc.ProcessId -eq 41001) { $ports = @(443,3074) }
        if ($proc.ProcessId -eq 41002) { $ports = @(8765) }
        foreach ($port in $ports) {
            [pscustomobject]@{LocalAddress='127.0.0.1'; LocalPort=$port; OwningProcess=$proc.ProcessId}
        }
    }
    if ($global:fixtureMode -eq 'tcp-conflict') {
        [pscustomobject]@{LocalAddress='0.0.0.0'; LocalPort=8765; OwningProcess=999}
    }
}
function Get-NetUDPEndpoint {
    if ($global:fixtureMode -eq 'udp-conflict') {
        [pscustomobject]@{LocalAddress='0.0.0.0'; LocalPort=3074; OwningProcess=999}
    }
    if ($global:fixtureMode -ne 'partial' -and ($global:fixtureProcesses.ProcessId -contains 41001)) {
        [pscustomobject]@{LocalAddress='127.0.0.1'; LocalPort=3074; OwningProcess=41001}
    }
}
function Invoke-RestMethod {
    param($Uri, $TimeoutSec, [switch]$UseBasicParsing)
    if ($global:fixtureMode -eq 'bad-api') { return [pscustomobject]@{error='wrong application'} }
    return [pscustomobject]@{profiles=@(); game_running=$false; capabilities=@{}}
}
function Invoke-WebRequest {
    param($Uri, $TimeoutSec, [switch]$UseBasicParsing)
    if ($global:fixtureMode -eq 'bad-ui') { throw 'UI unavailable' }
    return [pscustomobject]@{StatusCode=200; Content=(Get-Content (Join-Path $global:fixtureRoot 'web\dist\index.html') -Raw)}
}
$code = 0
try {
    INVOCATION
    REPEAT
} catch {
    Write-Output ('FAILURE: ' + $_.Exception.Message)
    $code = 1
}
Write-Output ('EVENTS:' + (ConvertTo-Json -InputObject @($global:launchEvents) -Compress -Depth 5))
exit $code
'''.replace('MODE', literal(mode)).replace(
            'INVOCATION', "& (Join-Path $PSScriptRoot 'Start.ps1') "
            + (f'-PythonPath {literal(python_path)} ' if python_path else '')
            + '-StartupTimeoutSeconds 1 ' + ' '.join(flags)).replace(
            'REPEAT', "& (Join-Path $PSScriptRoot 'Start.ps1') "
            + (f'-PythonPath {literal(python_path)} ' if python_path else '')
            + '-StartupTimeoutSeconds 1 ' + ' '.join(flags) if repeat else ''), encoding='utf-8-sig')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(harness)],
                                cwd=self.root.parent, capture_output=True, timeout=25)
        output = result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace')
        events = next((line[7:] for line in output.splitlines() if line.startswith('EVENTS:')), '[]')
        return result.returncode, json.loads(events), output

    def test_check_only_never_starts_processes_or_creates_runtime_logs(self):
        code, events, output = self.run_launcher('-CheckOnly')
        self.assertEqual(code, 0, output)
        self.assertEqual(events, [])
        self.assertFalse((self.root / 'runtime/logs').exists())

    def test_path_python_selection_and_missing_interpreter(self):
        code, events, output = self.run_launcher('-CheckOnly', python_path=None)
        self.assertEqual(code, 0, output)
        self.assertEqual(events, [])
        code, events, output = self.run_launcher(python_path=str(self.root / 'missing-python.exe'))
        self.assertNotEqual(code, 0, output)
        self.assertEqual(events, [])
        self.assertIn('-PythonPath', output)

    def test_venv_redirector_and_worker_are_one_service_and_reused(self):
        subprocess.run([sys.executable, '-m', 'venv', '--without-pip', '--system-site-packages', str(self.root / '.venv')],
                       check=True, capture_output=True, timeout=30)
        code, events, output = self.run_launcher('-NoGame', '-NoBrowser', mode='venv', repeat=True, python_path=None)
        self.assertEqual(code, 0, output)
        self.assertEqual(len(events), 1, events)
        self.assertTrue(all('.venv' in event['file'] for event in events))

    def test_missing_prerequisite_aborts_before_any_process_is_started(self):
        (self.root / 'web/dist/index.html').unlink()
        code, events, output = self.run_launcher()
        self.assertNotEqual(code, 0, output)
        self.assertEqual(events, [])
        self.assertIn('npm run build', output)

    def test_tcp_and_udp_conflicts_report_owner_without_starting_anything(self):
        for mode, port in [('tcp-conflict', '8765'), ('udp-conflict', '3074')]:
            with self.subTest(mode=mode):
                code, events, output = self.run_launcher(mode=mode)
                self.assertNotEqual(code, 0, output)
                self.assertEqual(events, [])
                self.assertIn(port, output)
                self.assertIn('999', output)

    def test_default_starts_both_hidden_services_browser_and_elevated_game(self):
        code, events, output = self.run_launcher()
        self.assertEqual(code, 0, output)
        self.assertEqual(len(events), 5, events)
        self.assertIn('controller.py', ' '.join(events[0]['arguments']))
        self.assertIn('local_server.py', ' '.join(events[1]['arguments']))
        for event in events[:2]:
            self.assertEqual(event['file'], sys.executable)
            self.assertEqual(event['window'], 'Hidden')
        self.assertTrue(any(event['file'] == 'http://127.0.0.1:8765/' for event in events))
        self.assertTrue(any(event['verb'] == 'RunAs' for event in events))

    def test_no_game_no_browser_and_repeat_reuse_services(self):
        code, events, output = self.run_launcher('-NoGame', '-NoBrowser', repeat=True)
        self.assertEqual(code, 0, output)
        self.assertEqual(len(events), 1, events)

    def test_repeated_default_launch_reuses_game(self):
        code, events, output = self.run_launcher(repeat=True)
        self.assertEqual(code, 0, output)
        self.assertEqual(sum(event['verb'] == 'RunAs' for event in events), 1)
        self.assertEqual(sum(event['window'] == 'Hidden' for event in events), 3)

    def test_existing_services_without_pid_files_are_adopted(self):
        code, events, output = self.run_launcher('-NoBrowser', mode='existing')
        self.assertEqual(code, 0, output)
        self.assertEqual(len(events), 2, events)
        self.assertEqual(events[0]['verb'], 'RunAs')

    def test_stale_pid_files_do_not_block_startup(self):
        self.write(self.root / 'runtime/logs/server.pid', '9999')
        self.write(self.root / 'runtime/logs/controller.pid', '9999')
        code, events, output = self.run_launcher('-NoGame', '-NoBrowser')
        self.assertEqual(code, 0, output)
        self.assertEqual(len(events), 1)

    def test_crash_partial_service_and_bad_http_do_not_open_browser_or_game(self):
        for mode in ('crash', 'partial', 'bad-api', 'bad-ui'):
            with self.subTest(mode=mode):
                code, events, output = self.run_launcher(mode=mode)
                self.assertNotEqual(code, 0, output)
                self.assertFalse(any(event['verb'] == 'RunAs' or event['file'].startswith('http') for event in events))
                self.assertIn('logs', output)

    def test_uac_cancellation_is_a_failure_and_keeps_service_diagnostics(self):
        code, events, output = self.run_launcher(mode='cancel')
        self.assertNotEqual(code, 0, output)
        self.assertIn('UAC cancelled', output)
        self.assertIn('logs', output)


if __name__ == '__main__':
    unittest.main()
