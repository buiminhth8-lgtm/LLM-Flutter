param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8000,
  [string]$Python = "",
  [string]$Config = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Python)) {
  if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
  } elseif (Test-Path ".\venv\Scripts\python.exe") {
    $Python = ".\venv\Scripts\python.exe"
  } else {
    $Python = "python"
  }
}

& $Python -c "import sys; print(sys.executable)"
& $Python -c "import llm_studio; print(llm_studio.__file__)"
& $Python -c "import uvicorn; print(uvicorn.__version__)"

$argsList = @(
  "-m", "llm_studio.server",
  "--host", $HostName,
  "--port", "$Port"
)

if (-not [string]::IsNullOrWhiteSpace($Config)) {
  $argsList += @("--config", $Config)
}

& $Python @argsList
