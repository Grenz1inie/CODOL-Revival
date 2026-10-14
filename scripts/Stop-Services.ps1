$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$serverFile = Join-Path $projectRoot 'src\local_server.py'
$pidFile = Join-Path $projectRoot 'runtime\logs\server.pid'
if (!(Test-Path -LiteralPath $pidFile)) { return }
$savedPid = [int](Get-Content -LiteralPath $pidFile)
$existing = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
if ($existing -and $existing.CommandLine.Contains($serverFile)) {
    Stop-Process -Id $savedPid
    Write-Output "Local service stopped (PID $savedPid)."
}
