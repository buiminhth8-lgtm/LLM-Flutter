$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  throw "Flutter SDK was not found in PATH."
}

$python = Join-Path "$PSScriptRoot\.." ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
  throw "Python virtual environment was not found. Run scripts/setup_windows_python312.ps1 first."
}

Write-Host "Starting Flutter Windows client. The client will start python -m llm_studio.server when needed."
& "$PSScriptRoot\flutter_run_windows.ps1"
