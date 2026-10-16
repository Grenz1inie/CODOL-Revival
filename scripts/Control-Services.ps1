param(
    [ValidateSet('status', 'start', 'stop')][string]$Action = 'status',
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$projectRoot = Split-Path $PSScriptRoot -Parent
$serverFile = Join-Path $projectRoot 'src\local_server.py'
$pidFile = Join-Path $projectRoot 'runtime\logs\server.pid'

function Get-OwnedServer {
    $pattern = '(?i)(?:^|\s|\")' + [regex]::Escape($serverFile) + '(?:\"|\s|$)'
    $matches = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match $pattern })
    # Windows venv Python can have a redirector parent with the same command line.
    $leaves = @($matches | Where-Object { $_.ProcessId -notin $matches.ParentProcessId })
    if ($leaves.Count -gt 1) { throw 'Multiple local server processes found; resolve duplicates before controlling the server.' }
    if ($leaves.Count) { return $leaves[0] }
}

function Get-ServerState {
    $owned = Get-OwnedServer
    $tcp = @(Get-NetTCPConnection -State Listen)
    $udp = @(Get-NetUDPEndpoint)
    $ports = @(foreach ($endpoint in @(@('auth','TCP',443), @('lobby','TCP',3074), @('stun','UDP',3074))) {
        $listeners = if ($endpoint[1] -eq 'TCP') { $tcp } else { $udp }
        $listeners = @($listeners | Where-Object {
            $_.LocalPort -eq $endpoint[2] -and $_.LocalAddress -in @('127.0.0.1','0.0.0.0','::','::1')
        })
        @{
            name = $endpoint[0]; protocol = $endpoint[1]; port = $endpoint[2]
            listening = [bool]($owned -and @($listeners | Where-Object OwningProcess -eq $owned.ProcessId).Count)
            conflict = [bool]@($listeners | Where-Object { !$owned -or $_.OwningProcess -ne $owned.ProcessId }).Count
        }
    })
    return @{
        running = [bool]$owned
        pid = $(if ($owned) { [int]$owned.ProcessId } else { $null })
        ready = [bool]($owned -and !@($ports | Where-Object { !$_.listening -or $_.conflict }).Count)
        ports = $ports
    }
}

$state = Get-ServerState
if ($Action -eq 'start') {
    if (@($state.ports | Where-Object conflict).Count) { throw 'Required server ports are occupied by another process.' }
    if (!$state.running) {
        # Discard only this service's stale PID; Start-Services must not reuse a foreign process.
        if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile }
        & (Join-Path $PSScriptRoot 'Start-Services.ps1') -PythonPath $PythonPath | Out-Null
    }
    $timer = [Diagnostics.Stopwatch]::StartNew()
    do {
        $state = Get-ServerState
        if (!$state.running) { throw 'Local server exited before its ports were listening. See runtime/logs/server.stderr.log.' }
        if ($state.ready) { break }
        Start-Sleep -Milliseconds 300
    } while ($timer.Elapsed.TotalSeconds -lt 20)
    if (!$state.ready) { throw 'Local server did not open all required ports within 20 seconds. See runtime/logs/server.stderr.log.' }
    New-Item -ItemType Directory -Path (Split-Path $pidFile) -Force | Out-Null
    $state.pid | Set-Content -LiteralPath $pidFile
} elseif ($Action -eq 'stop' -and $state.running) {
    # Resolve the owned process again immediately before stopping; never trust a PID file.
    $owned = Get-OwnedServer
    if ($owned) { Stop-Process -Id $owned.ProcessId -Force }
    $state = Get-ServerState
    if ($state.running) { throw 'Local server is still running; stop did not complete.' }
    if (Test-Path -LiteralPath $pidFile) { Remove-Item -LiteralPath $pidFile }
}
$state | ConvertTo-Json -Depth 4 -Compress
