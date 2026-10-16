param([string]$PythonPath)
$ErrorActionPreference = 'Stop'
if (!$env:CODOL_REPO_ROOT -or !$env:CODOL_GAME_ROOT -or !$env:CODOL_RUNTIME) {
    throw 'Launch through the version manager.'
}
if (!$PythonPath) {
    $venvPython = Join-Path $env:CODOL_REPO_ROOT '.venv\Scripts\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe -ErrorAction Stop | Select-Object -First 1).Source }
}
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$ErrorActionPreference = 'Continue'
$output = & $PythonPath -B -X utf8 (Join-Path $PSScriptRoot '..\client\bootstrap.py') `
    --root $env:CODOL_REPO_ROOT --game $env:CODOL_GAME_ROOT --runtime $env:CODOL_RUNTIME 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($exitCode -ne 0) { throw ($output | Out-String) }
$output | Write-Output
