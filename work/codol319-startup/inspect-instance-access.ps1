$ErrorActionPreference = 'Stop'
$instance = 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\runtime\instances\codol-3.19.26.22-911c42a0027c'
$report = [ordered]@{user=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value}
$state = Join-Path $instance 'startup.json'
$report.state = [IO.File]::ReadAllText($state)
$report.acl = [IO.File]::GetAccessControl($state).Sddl
$report.attributes = [IO.File]::GetAttributes($state).ToString()
$report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $instance 'access-diagnosis.json') -Encoding UTF8
