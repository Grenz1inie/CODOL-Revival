"""Open the Windows directory dialog on explicit console requests."""
import json
import subprocess


def choose_folder():
    script = r'''
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Windows.Forms
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$dialog.Description = 'Select the game installation directory'
$dialog.ShowNewFolderButton = $false
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
$owner.ShowInTaskbar = $false
$owner.Opacity = 0
try {
    # Realize and activate the owner so the native dialog inherits its z-order.
    $owner.Show()
    $owner.Activate()
    $path = if ($dialog.ShowDialog($owner) -eq [Windows.Forms.DialogResult]::OK) { $dialog.SelectedPath } else { $null }
    @{path=$path} | ConvertTo-Json -Compress
} finally { $dialog.Dispose(); $owner.Dispose() }
'''
    result = subprocess.run(['powershell.exe', '-NoProfile', '-STA', '-Command', script],
                            capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=300)
    if result.returncode:
        raise OSError('无法打开目录选择窗口')
    return json.loads(result.stdout.decode('utf-8-sig'))['path']
