param(
    [ValidateSet('status')][string]$Action = 'status',
    [string]$PythonPath = 'python'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
& $PythonPath -B (Join-Path $PSScriptRoot '../client/launch.py') status --runtime $env:CODOL_RUNTIME
exit $LASTEXITCODE
