$ErrorActionPreference = "Stop"

Write-Host "Creating Python 3.12 virtual environment..."
py -3.12 -m venv .venv

Write-Host ""
Write-Host "Activate with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Upgrading packaging tools..."
& .\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

Write-Host "Base dependencies are not installed automatically."
Write-Host "Run: .\scripts\install_base.ps1"
