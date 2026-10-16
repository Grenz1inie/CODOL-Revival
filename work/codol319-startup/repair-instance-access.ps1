$ErrorActionPreference = 'Stop'
$instance = 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\runtime\instances\codol-3.19.26.22-911c42a0027c'
$account = '*S-1-5-21-2158203076-2459157416-2778051298-1001:(OI)(CI)M'
& icacls.exe $instance /grant $account /T /C *> (Join-Path $instance 'access-repair.log')
exit $LASTEXITCODE
