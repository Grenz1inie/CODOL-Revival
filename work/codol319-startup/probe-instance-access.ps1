$ErrorActionPreference = 'Stop'
$instance = 'E:\Games\CODOL_Experience_V3.3.3.3_FULL.7z\CODOL-Revival\runtime\instances\codol-3.19.26.22-911c42a0027c'
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$report = [ordered]@{}
$path = Join-Path $instance 'startup.json'
$acl = [IO.File]::GetAccessControl($path)
$report.before = $acl.Sddl
$rule = New-Object Security.AccessControl.FileSystemAccessRule($sid, 'Modify', 'Allow')
$acl.AddAccessRule($rule)
[IO.File]::SetAccessControl($path, $acl)
$report.after = [IO.File]::GetAccessControl($path).Sddl
$report | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $instance 'access-probe.json') -Encoding UTF8
