$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $projectRoot

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  throw "Missing .venv. Run scripts\setup_windows_python312.ps1 first."
}

$python = ".\.venv\Scripts\python.exe"
& $python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.12 x64 virtual environment is required." }

& $python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)"
if ($LASTEXITCODE -ne 0) { throw "CUDA PyTorch is required; CPU torch is not accepted." }

$flutter = (Get-Command flutter -ErrorAction SilentlyContinue).Source
if (-not $flutter) { throw "Flutter SDK was not found. Add flutter\bin to PATH." }

$apiBase = "http://127.0.0.1:8000"
$apiStartedByScript = $false
$apiProcess = $null

try {
  try {
    Invoke-RestMethod "$apiBase/health" -TimeoutSec 2 | Out-Null
    Write-Host "API is already running: $apiBase"
  } catch {
    Write-Host "Starting local API: $apiBase"
    $apiProcess = Start-Process -FilePath $python -ArgumentList @("-m", "llm_studio.cli", "serve", "--host", "127.0.0.1", "--port", "8000") -WindowStyle Hidden -PassThru
    $apiStartedByScript = $true
    for ($i = 0; $i -lt 60; $i++) {
      try {
        Invoke-RestMethod "$apiBase/health" -TimeoutSec 2 | Out-Null
        break
      } catch {
        Start-Sleep -Seconds 1
      }
      if ($i -eq 59) { throw "API startup timed out." }
    }
  }

  Push-Location "apps\flutter_studio"
  & flutter run -d windows --dart-define="LLM_STUDIO_API_BASE=$apiBase"
  if ($LASTEXITCODE -ne 0) { throw "Flutter client failed to start." }
} finally {
  Pop-Location -ErrorAction SilentlyContinue
  if ($apiStartedByScript -and $apiProcess -and -not $apiProcess.HasExited) {
    Stop-Process -Id $apiProcess.Id -Force
  }
}
