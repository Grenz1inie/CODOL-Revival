param(
    [ValidateSet('start','stop','watch')][string]$Action,
    [int]$GamePid,
    [string]$PythonPath,
    [ValidateRange(1,120)][int]$StartupTimeoutSeconds = 20
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$gameName = 'codoMP_client_shipRetail'
$services = Join-Path $PSScriptRoot 'Control-Services.ps1'

if ($Action -eq 'watch') {
    if ($GamePid -le 0) { throw 'A game PID is required.' }
    $watched = Get-Process -Id $GamePid -ErrorAction SilentlyContinue
    if ($watched) {
        if ($watched.ProcessName -ne $gameName) { throw 'The watched PID is not the game.' }
        # Wait on the process handle rather than polling or depending on an open browser.
        $watched.WaitForExit()
    }
}

# Serialize a new launch with the previous game's exit cleanup, across processes.
$hash = [Security.Cryptography.SHA256]::Create()
$key = [BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($projectRoot.ToLowerInvariant())))
$hash.Dispose()
$mutex = [Threading.Mutex]::new($false, ('Local\CODOL-Game-' + $key))
$locked = $false
try {
    try { $locked = $mutex.WaitOne(90000) } catch [Threading.AbandonedMutexException] { $locked = $true }
    if (!$locked) { throw 'Another game session operation is still in progress.' }
    if ($Action -eq 'start') {
        if (Get-Process -Name $gameName -ErrorAction SilentlyContinue) { throw 'The game is already running.' }
        $gameRoot = Join-Path (Split-Path $projectRoot -Parent) 'CODOL_Experience_V3.3.3.3_FULL.7z'
        $gameExe = Join-Path $gameRoot ($gameName + '.exe')
        $skipTutorial = $true
        $settingsFile = Join-Path $projectRoot 'runtime\data\controller.json'
        if (Test-Path -LiteralPath $settingsFile) {
            $settings = Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
            if ($settings.skip_tutorial -isnot [bool]) { throw 'Invalid skip_tutorial setting.' }
            $skipTutorial = $settings.skip_tutorial
        }
        $skipValue = if ($skipTutorial) { 1 } else { 0 }
        # Keep the verified single allowlisted command segment.
        $gameCommands = "+set dw_username johnClient;set 2822 $skipValue;set 3233 $skipValue"
        try {
            & $services -Action start -PythonPath $PythonPath -StartupTimeoutSeconds $StartupTimeoutSeconds | Out-Null
            $game = Start-Process -FilePath $gameExe -ArgumentList '-q','0','-src=tgp','-game_id','29','-zone_id','83886082', `
                $gameCommands -WorkingDirectory $gameRoot -Verb RunAs -PassThru
            if (!$game -or $game.HasExited) { throw 'The game exited during launch.' }
            Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden `
                -RedirectStandardError (Join-Path $projectRoot "runtime\logs\game-session-$($game.Id).stderr.log") -ArgumentList `
                '-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $PSCommandPath + '"'),'-Action','watch','-GamePid',$game.Id | Out-Null
        } catch {
            $launchFailure = $_
            if (!(Get-Process -Name $gameName -ErrorAction SilentlyContinue)) { & $services -Action stop | Out-Null }
            throw $launchFailure
        }
    } elseif ($Action -eq 'stop') {
        if (Get-Process -Name $gameName -ErrorAction SilentlyContinue) { & (Join-Path $PSScriptRoot 'Stop-Game.ps1') }
        if (Get-Process -Name $gameName -ErrorAction SilentlyContinue) { throw 'The game is still running; the server was kept running.' }
        & $services -Action stop | Out-Null
    } elseif (!(Get-Process -Name $gameName -ErrorAction SilentlyContinue)) {
        & $services -Action stop | Out-Null
    }
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
