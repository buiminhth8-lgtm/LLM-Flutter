param(
  [string]$BackendUrl = "http://127.0.0.1:8000",
  [switch]$Json
)

$ErrorActionPreference = "Continue"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$checks = @()

function Add-Check {
  param([string]$Name, [string]$Status, [string]$Message)
  $script:checks += [pscustomobject]@{
    name = $Name
    status = $Status
    message = $Message
  }
}

function Test-Command {
  param([string]$Name)
  $cmd = Get-Command $Name -ErrorAction SilentlyContinue
  return $null -ne $cmd
}

if (Test-Command "python") {
  $pythonVersion = & python --version 2>&1
  Add-Check "python" "ok" "$pythonVersion"
} else {
  Add-Check "python" "error" "python was not found on PATH."
}

if (Test-Command "flutter") {
  $flutterVersion = (& flutter --version 2>&1 | Select-Object -First 1)
  Add-Check "flutter" "ok" "$flutterVersion"
} else {
  Add-Check "flutter" "warning" "Flutter SDK was not found on PATH; backend validation can still run."
}

$dataDir = Join-Path $repoRoot "data"
try {
  New-Item -ItemType Directory -Force -Path $dataDir | Out-Null
  $probe = Join-Path $dataDir "stage12-write-probe.tmp"
  Set-Content -LiteralPath $probe -Value "ok" -Encoding UTF8
  Remove-Item -LiteralPath $probe -Force
  Add-Check "data_dir" "ok" "Data directory is writable."
} catch {
  Add-Check "data_dir" "error" "Data directory is not writable: $($_.Exception.Message)"
}

try {
  $response = Invoke-RestMethod -Uri "$BackendUrl/v1/health" -Method Get -TimeoutSec 5
  Add-Check "backend_health" "ok" "Backend /v1/health returned $($response.status)."
} catch {
  Add-Check "backend_health" "warning" "Backend is not reachable at $BackendUrl; start it with start_backend.ps1."
}

$overall = if ($checks.status -contains "error") { "error" } elseif ($checks.status -contains "warning") { "warning" } else { "ok" }
$payload = [pscustomobject]@{
  status = $overall
  repo_root = "<repo-root>"
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  checks = $checks
}

if ($Json) {
  $payload | ConvertTo-Json -Depth 5
} else {
  "LLM Studio Windows environment check: $overall"
  $checks | Format-Table -AutoSize
}

if ($overall -eq "error") {
  exit 1
}
