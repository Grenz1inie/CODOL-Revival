$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$serverFile = Join-Path $projectRoot 'src\controller.py'
$logRoot = Join-Path $projectRoot 'runtime\logs'
$pidFile = Join-Path $logRoot 'controller.pid'
if (!(Test-Path (Join-Path $projectRoot 'web\dist\index.html'))) {
    throw 'Build the UI first: cd web; npm ci; npm run build'
}
if (Test-Path -LiteralPath $pidFile) {
    $savedPid = [int](Get-Content -LiteralPath $pidFile)
    $existing = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
    if ($existing -and $existing.CommandLine.Contains($serverFile)) {
        Write-Output 'Controller already running: http://127.0.0.1:8765'
        return
    }
}
$venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
$pythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe).Source }
New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
$controllerProc = Start-Process -FilePath $pythonPath -ArgumentList '-B','-u',('"' + $serverFile + '"') `
    -WorkingDirectory $projectRoot -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $logRoot 'controller.stdout.log') `
    -RedirectStandardError (Join-Path $logRoot 'controller.stderr.log') -PassThru
$controllerProc.Id | Set-Content -LiteralPath $pidFile
Write-Output 'Controller: http://127.0.0.1:8765'
