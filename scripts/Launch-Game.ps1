$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$gameRoot = Join-Path (Split-Path $projectRoot -Parent) 'CODOL_Experience_V3.3.3.3_FULL.7z'
$gameExe = Join-Path $gameRoot 'codoMP_client_shipRetail.exe'
if (Get-Process -Name 'codoMP_client_shipRetail' -ErrorAction SilentlyContinue) {
    throw 'Close the current game window before launching another test.'
}
& (Join-Path $PSScriptRoot 'Start-Services.ps1')
# Keep one allowlisted command segment; the engine later executes its semicolon list.
# See docs/wiki/06-onboarding-profile.md for the failed direct flags and live proof.
$skipTutorial = $true
$settingsFile = Join-Path $projectRoot 'runtime\data\controller.json'
if (Test-Path -LiteralPath $settingsFile) {
    $settings = Get-Content -LiteralPath $settingsFile -Raw | ConvertFrom-Json
    if ($settings.skip_tutorial -isnot [bool]) { throw 'Invalid skip_tutorial setting.' }
    $skipTutorial = $settings.skip_tutorial
}
$skipValue = if ($skipTutorial) { 1 } else { 0 }
$gameCommands = "+set dw_username johnClient;set 2822 $skipValue;set 3233 $skipValue"
Start-Process -FilePath $gameExe -ArgumentList '-q','0','-src=tgp','-game_id','29','-zone_id','83886082', `
    $gameCommands `
    -WorkingDirectory $gameRoot -Verb RunAs -PassThru
