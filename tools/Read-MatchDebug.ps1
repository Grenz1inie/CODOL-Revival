param([switch]$Stats, [switch]$Connection)
$ErrorActionPreference = 'Stop'
$rootPath = Split-Path $PSScriptRoot -Parent
$expectedExe = Join-Path (Split-Path $rootPath -Parent) 'CODOL_Experience_V3.3.3.3_FULL.7z/codoMP_client_shipRetail.exe'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (!$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    $arguments = @('-NoProfile','-File',('"'+$PSCommandPath+'"'))
    if ($Stats) { $arguments += '-Stats' }
    if ($Connection) { $arguments += '-Connection' }
    Start-Process powershell.exe -Verb RunAs -WindowStyle Hidden -ArgumentList $arguments
    return
}
$game = @(Get-CimInstance Win32_Process -Filter "Name='codoMP_client_shipRetail.exe'" | Where-Object {
    $_.ExecutablePath -and [IO.Path]::GetFullPath($_.ExecutablePath) -ieq [IO.Path]::GetFullPath($expectedExe)
})
if ($game.Count -ne 1) { throw 'Expected one verified CODOL process.' }
if ((Get-FileHash -LiteralPath $expectedExe -Algorithm SHA256).Hash -ne 'e3823fd6afc80fb25fa84747e6e9634707b9a0b189357a5466921cda354af37b') { throw 'Client hash mismatch.' }
$cdb = 'C:/Program Files (x86)/Windows Kits/10/Debuggers/x86/cdb.exe'
$outputPath = Join-Path $rootPath 'runtime/logs/match-debug.txt'
if ($Stats) {
    # Three hardware execution breakpoints: no EXE/code-byte changes. Capture
    # only the 32 KiB public stats buffer around CRC/preparation, then detach.
    $capturePath = (Join-Path $rootPath ('runtime/captures/stats-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))).Replace('\', '/')
    $commands = @(
        ('ba e 1 codoMP_client_shipRetail+0x2d81bf ".writemem ' + $capturePath + '-before.bin @edi+0x7c L8000; gc"'),
        ('ba e 1 codoMP_client_shipRetail+0x2d81c4 ".writemem ' + $capturePath + '-crc.bin @edi+0x7c L8000; gc"'),
        ('ba e 1 codoMP_client_shipRetail+0x2d81ca ".writemem ' + $capturePath + '-prepared.bin @edi+0x7c L8000; bc *; qd"'),
        'g'
    )
    # Command file keeps debugger quoting separate from PowerShell quoting.
    $commandPath = $capturePath + '.cdb'
    $commands | Set-Content -LiteralPath $commandPath -Encoding Ascii
    # If a debugger command fails, its next prompt detaches instead of leaving
    # the game suspended. Normal completion detaches at the third breakpoint.
    'qd' | & $cdb -G -p $game[0].ProcessId -cf $commandPath *> $outputPath
    return
}
# Read the current state and netchan counters without suspending the client.
if ($Connection) {
    & $cdb -pv -p $game[0].ProcessId -c 'dd codoMP_client_shipRetail+0x162e7d0 L10; dd codoMP_client_shipRetail+0x29f7d90 L1; r @$t0 = poi(codoMP_client_shipRetail+0x162a538) ^ 0xd362501f; dd @$t0 L18; dd @$t0+0x140 L2; da @$t0+0x148+0x400*((poi(@$t0+0x144)+1)&0xff) L100; da @$t0+0x148+0x400*(poi(@$t0+0x140)&0xff) L100; dd @$t0+0x40140 L8; dd @$t0+0x80158 L10; r @$t1 = poi(codoMP_client_shipRetail+0x162e838) ^ 0x6891d1c7; dd @$t1+0x3530 L1c; dd @$t1+0x625c L1; r @$t7 = poi(@$t1+0x867c) ^ 0x96b9dc91; r @$t8 = (poi(@$t0+0x80158)-1) & poi(@$t1+0x8668); dd @$t7+@$t8*0xc L3; dd codoMP_client_shipRetail+0x74b0a50 L3; dd poi(codoMP_client_shipRetail+0x162e7cc)+0xc L1; dd @$t1+0x365c+0x2c*(poi(@$t1+0x625c)&0xff) Lb; r @$t2 = poi(codoMP_client_shipRetail+0x1619510+4*poi(codoMP_client_shipRetail+0x7417ba8)) ^ 0xfbb2c97a; dd @$t2 L18; dd @$t2+0x140 L10; dd @$t2+0x1f0 L4; dd @$t2+0x340 L4; dd @$t2+0x98 L1; dd @$t2+0x190 L4; dd @$t2+0x2a4 L10; dd @$t2+0x2e0 L4; dd @$t2+0x3350 L1; dd @$t2+0xbd00c L1; dd @$t2+0xbd72c L8; r @$t4 = poi(codoMP_client_shipRetail+0x13f5a40+5*4); dd @$t4 L10; dd @$t1+0x18 L1; dd @$t2+0xae4d4 L1; dd @$t2+0x16c074 L1; dd @$t2+0xf0 L1; dd poi(codoMP_client_shipRetail+0x13e2c5c)+0xc L1; dd poi(codoMP_client_shipRetail+0x1619ecc)+0xc L1; r @$t5 = poi(codoMP_client_shipRetail+0x1619510+4*poi(codoMP_client_shipRetail+0x7417bb8)) ^ 0x39641402; dd @$t5 L8; r @$t6 = poi(@$t5); dd @$t6 L10; dd @$t6+0xc0 L8; dd poi(@$t6+0xc0) L2; db poi(poi(@$t6+0xc0))+0x15d L1; db poi(poi(@$t6+0xc0)+4)+0x15d L1; dd @$t6+0x9c L1; dd @$t2+0x3560 L20; dd @$t2+0xae4c4 L4; r @$t3 = poi(@$t2+0x357c); dd @$t3+0x140 L10; dd @$t3+0x1f0 L10; dd @$t3+0x250 L8; dd @$t3+0x340 L4; dd codoMP_client_shipRetail+0x74b0a40 L18; dd poi(codoMP_client_shipRetail+0x2a8cf68) L8; q' *> $outputPath
    return
}
# Noninvasive, nonsuspending attach: module inventory and thread stacks only.
& $cdb -pv -p $game[0].ProcessId -c 'lm; ~* k; q' *> $outputPath
