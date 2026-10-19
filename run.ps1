# Windows PowerShell Launcher for Xenon Hotel Management
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
}

if (-not $pythonCmd) {
    Write-Error "Python was not found in PATH. Please install Python 3.10+."
    exit 1
}

Write-Host "Starting Xenon Hotel Management on Windows via $pythonCmd..." -ForegroundColor DarkYellow
& $pythonCmd "$PSScriptRoot\run.py"
