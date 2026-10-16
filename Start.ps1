#requires -Version 5.1
<#
.SYNOPSIS
Check the environment, start local services and the controller, then open the game.
.EXAMPLE
.\Start.ps1
.EXAMPLE
.\Start.ps1 -CheckOnly
.EXAMPLE
.\Start.ps1 -NoGame -NoBrowser
#>
[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$NoGame,
    [switch]$NoBrowser,
    [string]$PythonPath,
    [ValidateRange(1, 120)][int]$StartupTimeoutSeconds = 20
)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$logRoot = Join-Path $projectRoot 'runtime\logs'
$controllerUrl = 'http://127.0.0.1:8765/'

function Get-ServiceProcess($SourcePath) {
    $pattern = '(^|\s|")' + [regex]::Escape($SourcePath) + '(?=\s|$|")'
    $matching = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match $pattern })
    # Windows venv uses a redirector parent; the leaf process owns the sockets.
    $workers = @($matching | Where-Object { $matching.ParentProcessId -notcontains $_.ProcessId })
    if ($workers.Count -gt 1) { throw "Multiple processes run $SourcePath. Close the duplicate before starting." }
    if ($workers.Count) { return $workers[0] }
}

function Get-StartupListeners {
    Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Select-Object @{Name='Protocol'; Expression={'TCP'}}, LocalAddress, LocalPort, OwningProcess
    Get-NetUDPEndpoint -ErrorAction Stop |
        Select-Object @{Name='Protocol'; Expression={'UDP'}}, LocalAddress, LocalPort, OwningProcess
}

function Test-ServicePorts($Service, $Listeners, [switch]$RequireAll) {
    foreach ($protocol in @('TCP', 'UDP')) {
        foreach ($port in $Service[$protocol]) {
            $owners = @($Listeners | Where-Object {
                $_.Protocol -eq $protocol -and $_.LocalPort -eq $port -and
                $_.LocalAddress -in @('127.0.0.1', '0.0.0.0', '::')
            })
            foreach ($owner in $owners) {
                if (!$Service.Process -or $owner.OwningProcess -ne $Service.Process.ProcessId) {
                    throw "$protocol port $port is occupied by PID $($owner.OwningProcess). Close that application or resolve the conflict first."
                }
            }
            if ($RequireAll -and !$owners.Count) { return $false }
        }
    }
    return $true
}

try {
    if ($env:OS -ne 'Windows_NT') { throw 'Start.ps1 requires Windows.' }
    if (!$PythonPath) {
        $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
        $PythonPath = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python.exe' }
    }
    $pythonCommand = Get-Command $PythonPath -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (!$pythonCommand) { throw "Python was not found: $PythonPath. Install Python or supply -PythonPath." }
    $PythonPath = $pythonCommand.Source
    Write-Output "Checking environment with $PythonPath"
    & $PythonPath -B (Join-Path $projectRoot 'tools\check-startup.py')
    if ($LASTEXITCODE -ne 0) { throw 'Environment check failed. Resolve the reported prerequisites and run Start.ps1 again.' }

    $services = @(
        @{Name='Local services'; Source='src\local_server.py'; Entry='Start-Services.ps1';
          PidFile='server.pid'; TCP=@(443,3074); UDP=@(3074); Process=$null},
        @{Name='Web controller'; Source='src\controller.py'; Entry='Start-Controller.ps1';
          PidFile='controller.pid'; TCP=@(8765); UDP=@(); Process=$null}
    )
    $listeners = @(Get-StartupListeners)
    foreach ($service in $services) {
        $sourcePath = Join-Path $projectRoot $service.Source
        $service.Process = Get-ServiceProcess $sourcePath
        Test-ServicePorts $service $listeners | Out-Null
    }
    if ($CheckOnly) {
        Write-Output '[OK] Preflight passed. No services, game or browser were started.'
        return
    }

    New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
    foreach ($service in @($services | Where-Object Entry -eq 'Start-Controller.ps1')) {
        $pidFile = Join-Path $logRoot $service.PidFile
        if ($service.Process) {
            # Recover missing/stale PID metadata for the existing stop/launch scripts.
            $service.Process.ProcessId | Set-Content -LiteralPath $pidFile
            Write-Output "$($service.Name) already running (PID $($service.Process.ProcessId))."
        } else {
            & (Join-Path $projectRoot ('scripts\' + $service.Entry)) -PythonPath $PythonPath
        }

        $timer = [Diagnostics.Stopwatch]::StartNew()
        $ready = $false
        $lastFailure = 'Waiting for all required listeners.'
        do {
            $service.Process = Get-ServiceProcess (Join-Path $projectRoot $service.Source)
            if (!$service.Process -or !(Get-Process -Id $service.Process.ProcessId -ErrorAction SilentlyContinue)) {
                throw "$($service.Name) exited during startup. See $logRoot."
            }
            $ready = Test-ServicePorts $service @(Get-StartupListeners) -RequireAll
            if ($ready -and $service.Entry -eq 'Start-Controller.ps1') {
                try {
                    $status = Invoke-RestMethod ($controllerUrl + 'api/status') -TimeoutSec 2
                    if ($status.game_running -isnot [bool] -or !$status.PSObject.Properties['profiles']) {
                        throw 'Unexpected controller /api/status response.'
                    }
                    $page = Invoke-WebRequest $controllerUrl -UseBasicParsing -TimeoutSec 2
                    if ($page.StatusCode -ne 200 -or !$page.Content) { throw 'Controller UI is unavailable.' }
                } catch {
                    $ready = $false
                    $lastFailure = $_.Exception.Message
                }
            }
            if (!$ready) { Start-Sleep -Milliseconds 300 }
        } while (!$ready -and $timer.Elapsed.TotalSeconds -lt $StartupTimeoutSeconds)
        if (!$ready) { throw "$($service.Name) did not become ready. $lastFailure See $logRoot." }
        $service.Process.ProcessId | Set-Content -LiteralPath $pidFile
        Write-Output "[OK] $($service.Name) ready (PID $($service.Process.ProcessId))."
    }

    Write-Output "Controller: $controllerUrl"
    if (!$NoGame) {
        if (Get-Process -Name 'codoMP_client_shipRetail' -ErrorAction SilentlyContinue) {
            Write-Output 'Game already running; keeping the current session.'
        } else {
            & (Join-Path $projectRoot 'scripts\Launch-Game.ps1') -PythonPath $PythonPath -StartupTimeoutSeconds $StartupTimeoutSeconds | Out-Null
            Write-Output 'Game launch requested. Confirm Windows UAC if prompted.'
        }
    }
    if (!$NoBrowser) { Start-Process -FilePath $controllerUrl }
    Write-Output "Startup complete. Logs: $logRoot"
} catch {
    throw "Startup failed: $($_.Exception.Message) Logs: $logRoot. Services already started are kept running."
}
