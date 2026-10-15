$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$serverFile = Join-Path $projectRoot 'src\local_server.py'
$pidFile = Join-Path $projectRoot 'runtime\logs\server.pid'
$nativeFile = Join-Path $projectRoot 'runtime\logs\native-instance.json'
if (Test-Path -LiteralPath $nativeFile) {
    $native = Get-Content -LiteralPath $nativeFile -Raw | ConvertFrom-Json
    $stageRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'research\experiments\story-native')) + '\'
    $nativeHome = [IO.Path]::GetFullPath($native.home)
    if (!$nativeHome.StartsWith($stageRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Native instance path is outside the isolated workspace.'
    }
    $nativeProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$native.pid)"
    if ($nativeProcess -and $nativeProcess.ExecutablePath -eq (Join-Path $nativeHome 'server3333.exe')) {
        Stop-Process -Id $nativeProcess.ProcessId
        Write-Output "Native instance stopped (PID $($nativeProcess.ProcessId))."
    }
}
if (!(Test-Path -LiteralPath $pidFile)) { return }
$savedPid = [int](Get-Content -LiteralPath $pidFile)
$existing = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
if ($existing -and $existing.CommandLine.Contains($serverFile)) {
    Stop-Process -Id $savedPid
    Write-Output "Local service stopped (PID $savedPid)."
}
