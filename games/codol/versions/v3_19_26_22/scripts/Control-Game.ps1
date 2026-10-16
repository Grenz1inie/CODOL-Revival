param(
    [ValidateSet('start', 'stop')][string]$Action,
    [string]$PythonPath = 'python'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
& $PythonPath -B (Join-Path $PSScriptRoot '../client/launch.py') $Action --runtime $env:CODOL_RUNTIME --source $env:CODOL_GAME_ROOT
exit $LASTEXITCODE
