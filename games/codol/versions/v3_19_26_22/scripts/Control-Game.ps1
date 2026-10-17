param(
    [ValidateSet('start', 'stop')][string]$Action,
    [string]$PythonPath = 'python'
)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
# Start-Process -Wait: the controller may run under pythonw.exe, a GUI-subsystem
# binary that `&` does not wait for, which used to hide launch failures behind
# a stale $LASTEXITCODE of 0 ("launch incomplete, game not running").
$script = Join-Path $PSScriptRoot '../client/launch.py'
$run = Start-Process -FilePath $PythonPath -ArgumentList @('-B', $script, $Action,
    '--runtime', $env:CODOL_RUNTIME, '--source', $env:CODOL_GAME_ROOT) -Wait -PassThru -NoNewWindow
exit $run.ExitCode
