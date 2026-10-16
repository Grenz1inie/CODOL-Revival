param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$projectRoot = $env:CODOL_REPO_ROOT
$runtimeRoot = $env:CODOL_RUNTIME
if (!$projectRoot -or !$runtimeRoot) { throw 'Launch through the version manager.' }
$serverFile = Join-Path $projectRoot 'games\codol\versions\v3_3_3_3\server\local_server.py'
$logRoot = Join-Path $runtimeRoot 'logs'
$pidFile = Join-Path $logRoot 'server.pid'
if (Test-Path -LiteralPath $pidFile) {
    $savedPid = [int](Get-Content -LiteralPath $pidFile)
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
    if ($existing -and $existing.CommandLine.Contains($serverFile) -and $existing.CommandLine.Contains($runtimeRoot)) {
        Write-Output "Local service already running (PID $savedPid)."
        return
    }
}
if (!$PythonPath) {
    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe -ErrorAction Stop).Source }
}
& (Join-Path $PSScriptRoot 'Prepare-Client.ps1') -PythonPath $PythonPath | Out-Null
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $runtimeRoot 'captures') -Force | Out-Null
$serverPid = & $PythonPath -B (Join-Path $projectRoot 'src/manager/background.py') --cwd $projectRoot `
    --stdout (Join-Path $logRoot 'server.stdout.log') --stderr (Join-Path $logRoot 'server.stderr.log') `
    -- $PythonPath -B -u $serverFile --runtime $runtimeRoot
if ($LASTEXITCODE -ne 0) { throw 'Background service failed to start.' }
$serverPid | Set-Content -LiteralPath $pidFile
Write-Output "Local service started (PID $serverPid); see $logRoot\server.jsonl."
