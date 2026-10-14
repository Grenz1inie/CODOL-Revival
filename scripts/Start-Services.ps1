param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$serverFile = Join-Path $projectRoot 'src\local_server.py'
$logRoot = Join-Path $projectRoot 'runtime\logs'
$pidFile = Join-Path $logRoot 'server.pid'
if (Test-Path -LiteralPath $pidFile) {
    $savedPid = [int](Get-Content -LiteralPath $pidFile)
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
    if ($existing -and $existing.CommandLine.Contains($serverFile)) {
        Write-Output "Local service already running (PID $savedPid)."
        return
    }
}
if (!$PythonPath) {
    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe -ErrorAction Stop).Source }
}
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $projectRoot 'runtime\captures') -Force | Out-Null
$serverProc = Start-Process -FilePath $PythonPath `
    -ArgumentList '-B','-u', ('"' + $serverFile + '"') -WorkingDirectory $projectRoot `
    -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logRoot 'server.stdout.log') `
    -RedirectStandardError (Join-Path $logRoot 'server.stderr.log') -PassThru
$serverProc.Id | Set-Content -LiteralPath $pidFile
Write-Output "Local service started (PID $($serverProc.Id)); see runtime\logs\server.jsonl."
