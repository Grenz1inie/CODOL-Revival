$ErrorActionPreference = 'Stop'
$projectRoot = $env:CODOL_REPO_ROOT
$runtimeRoot = $env:CODOL_RUNTIME
if (!$projectRoot -or !$runtimeRoot) { throw 'Launch through the version manager.' }
$serverFile = Join-Path $projectRoot 'games\codol\versions\v3_3_3_3\server\local_server.py'
$pidFile = Join-Path $runtimeRoot 'logs\server.pid'
$nativeFile = Join-Path $runtimeRoot 'logs\native-instance.json'
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
