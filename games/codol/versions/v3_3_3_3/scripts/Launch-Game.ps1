param([string]$PythonPath, [ValidateRange(1,120)][int]$StartupTimeoutSeconds = 20)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Control-Game.ps1') -Action start -PythonPath $PythonPath -StartupTimeoutSeconds $StartupTimeoutSeconds
