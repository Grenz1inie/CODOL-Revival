param([string]$GameDirectory = $env:CODOL_GAME_ROOT, [string]$RuntimeDirectory = $env:CODOL_RUNTIME)
$ErrorActionPreference = 'Stop'
$runtimeRoot = $RuntimeDirectory
if (!$GameDirectory -or !$runtimeRoot) { throw 'Launch through the version manager.' }
$gameRoot = $GameDirectory
$expectedExe = [IO.Path]::GetFullPath((Join-Path $gameRoot 'codoMP_client_shipRetail.exe'))
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $shellExe = (Get-Process -Id $PID).Path
    Start-Process -FilePath $shellExe -ArgumentList '-NoProfile','-File',('"' + $PSCommandPath + '"'), '-GameDirectory', ('"' + $GameDirectory + '"'), '-RuntimeDirectory', ('"' + $RuntimeDirectory + '"') `
        -Verb RunAs -WindowStyle Hidden -Wait
    return
}
foreach ($gameProc in Get-CimInstance Win32_Process -Filter "Name='codoMP_client_shipRetail.exe'") {
    if ($gameProc.ExecutablePath -and [IO.Path]::GetFullPath($gameProc.ExecutablePath) -ieq $expectedExe) {
        Stop-Process -Id $gameProc.ProcessId -Force
        $event = @{ time = (Get-Date).ToUniversalTime().ToString('o'); event = 'game_stopped'; pid = $gameProc.ProcessId; path = $expectedExe }
        $event | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $runtimeRoot 'logs\game-control.jsonl')
    }
}
