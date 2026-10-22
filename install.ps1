# Install or update aniworld-cli on Windows (mpv included):
#   irm https://raw.githubusercontent.com/dxmoc/aniworld-cli/main/install.ps1 | iex
#
# Unpacks the latest release zip to %LOCALAPPDATA%\aniworld-cli and adds that
# folder to the user PATH. Run it again to update. Watch history stays in
# %APPDATA%\aniworld-cli. Uninstall: delete the folder and its PATH entry.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # the progress bar slows downloads in PowerShell 5.1
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$dir = Join-Path $env:LOCALAPPDATA 'aniworld-cli'
$zip = Join-Path $env:TEMP 'aniworld-cli-windows.zip'

Write-Host '==> Downloading aniworld-cli (with mpv)'
Invoke-WebRequest 'https://github.com/dxmoc/aniworld-cli/releases/latest/download/aniworld-cli-windows.zip' -OutFile $zip -UseBasicParsing
if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
Expand-Archive $zip $dir
Remove-Item $zip

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $dir) {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$dir".Trim(';'), 'User')
    $env:Path += ";$dir"
}

Write-Host "==> Done: $(& (Join-Path $dir 'aniworld-cli.exe') --version)"
Write-Host '==> Start it with: aniworld-cli'
