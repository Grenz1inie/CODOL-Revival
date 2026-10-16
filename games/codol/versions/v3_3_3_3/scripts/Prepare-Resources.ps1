param(
    [string]$GameRoot = $env:CODOL_GAME_ROOT,
    [string]$PythonPath,
    [switch]$RequireServer
)
$ErrorActionPreference = 'Stop'
$projectRoot = $env:CODOL_REPO_ROOT
if (!$projectRoot) { $projectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..\..\..\..')) }
if (!$GameRoot) { throw 'Specify -GameRoot with the supported 3.3.3.3 game directory.' }
if (!$PythonPath) {
    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $PythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { (Get-Command python.exe -ErrorAction Stop).Source }
}
$arguments = @('-B', (Join-Path $PSScriptRoot '..\client\preparation.py'), '--root', $projectRoot, '--game', $GameRoot)
if ($RequireServer) { $arguments += '--require-server' }
# Capture native stderr as text as well, so callers receive the extraction reason.
$ErrorActionPreference = 'Continue'
$output = & $PythonPath @arguments 2>&1
$exitCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($exitCode -ne 0) { throw ($output | Out-String) }
$output | Write-Output
