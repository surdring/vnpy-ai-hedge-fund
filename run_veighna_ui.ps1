# VeighNa AI Desktop UI Launcher
# Run this script directly in PowerShell (NOT inside Trae terminal)
$ProjectRoot = "d:\develop\vnpy-ai-hedge-fund"
$PythonExe = "python"

# Set Qt platform plugin path explicitly
$PySide6Dir = "$env:APPDATA\Python\Python311\site-packages\PySide6"
if (Test-Path $PySide6Dir) {
    $env:QT_QPA_PLATFORM_PLUGIN_PATH = "$PySide6Dir\plugins"
    $env:PATH = "$PySide6Dir;$env:PATH"
}

Set-Location $ProjectRoot
Write-Host "Starting VeighNa Desktop UI with AI Hedge Fund plugin..." -ForegroundColor Cyan
Write-Host "Working directory: $ProjectRoot" -ForegroundColor Gray

python vnpy/examples/veighna_trader/run.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "Desktop UI exited with code $LASTEXITCODE" -ForegroundColor Red
    Read-Host "Press Enter to close"
}