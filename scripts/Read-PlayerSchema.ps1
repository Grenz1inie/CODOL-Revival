param([switch]$Marketplace, [switch]$WeaponProgression, [switch]$Pve, [switch]$Commands, [switch]$Netconst)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$logPath = Join-Path $root $(if ($Marketplace) { 'runtime\logs\marketplace-capture.log' } else { 'runtime\logs\player-schema.log' })
if ($WeaponProgression) { $logPath = Join-Path $root 'runtime\logs\weapon-progression-capture.log' }
if ($Pve) { $logPath = Join-Path $root 'runtime\logs\pve-capture.log' }
if ($Commands) { $logPath = Join-Path $root 'runtime\logs\commands-capture.log' }
if ($Netconst) { $logPath = Join-Path $root 'runtime\logs\netconst-capture.log' }
try {
$gamePath = Join-Path (Split-Path $root -Parent) 'CODOL_Experience_V3.3.3.3_FULL.7z\codoMP_client_shipRetail.exe'
$gameProcesses = @(Get-Process -Name codoMP_client_shipRetail -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $gamePath })
if ($gameProcesses.Count -ne 1) { throw 'Expected exactly one verified game process.' }
$imageBase = $gameProcesses[0].MainModule.BaseAddress.ToInt64()
$python = Join-Path $root '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { $python = (Get-Command python.exe).Source }
$ErrorActionPreference = 'Continue'
$captureArgs = @('--pid', $gameProcesses[0].Id, '--base', $imageBase)
if ($Marketplace) { $captureArgs += '--marketplace' }
if ($WeaponProgression) { $captureArgs += '--weapon-progression' }
if ($Pve) { $captureArgs += '--pve' }
if ($Commands) { $captureArgs += '--commands' }
if ($Netconst) { $captureArgs += '--netconst' }
& $python (Join-Path $root 'tools\read-player-schema.py') @captureArgs *>&1 | Set-Content -Encoding utf8 $logPath
$schemaExit = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($schemaExit -ne 0) { throw "Schema capture failed; see $logPath" }
} catch {
    $_ | Out-String | Add-Content -Encoding utf8 $logPath
    exit 1
}
