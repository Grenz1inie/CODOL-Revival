$ErrorActionPreference = 'Stop'
$rootPath = Split-Path $PSScriptRoot -Parent
$expectedExe = Join-Path (Split-Path $rootPath -Parent) 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList '-NoProfile','-File',('"'+$PSCommandPath+'"')
    return
}
$game = @(Get-CimInstance Win32_Process -Filter "Name='codoMP_client_shipRetail.exe'" | Where-Object {
    $_.ExecutablePath -and [IO.Path]::GetFullPath($_.ExecutablePath) -ieq [IO.Path]::GetFullPath($expectedExe)
})
if ($game.Count -ne 1) { throw 'Expected one verified CODOL process.' }
if ((Get-FileHash -LiteralPath $expectedExe -Algorithm SHA256).Hash -ne 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b') { throw 'Client hash mismatch.' }
$cdb = 'C:/Program Files (x86)/Windows Kits/10/Debuggers/x86/cdb.exe'
$outputPath = Join-Path $rootPath 'runtime/logs/match-debug.txt'
# Noninvasive, nonsuspending attach: module inventory and thread stacks only.
& $cdb -pv -p $game[0].ProcessId -c 'lm; ~* k; q' *> $outputPath
