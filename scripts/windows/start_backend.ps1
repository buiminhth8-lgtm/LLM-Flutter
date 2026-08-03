param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8000,
  [string]$Config = "",
  [switch]$Visible
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$logDir = Join-Path $repoRoot "data\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stdout = Join-Path $logDir "backend.stdout.log"
$stderr = Join-Path $logDir "backend.stderr.log"

$arguments = @("-m", "llm_studio.server", "--host", $HostName, "--port", "$Port")
if ($Config.Trim().Length -gt 0) {
  $arguments += @("--config", $Config)
}

Push-Location $repoRoot
try {
  $startInfo = @{
    FilePath = "python"
    ArgumentList = $arguments
    PassThru = $true
    RedirectStandardOutput = $stdout
    RedirectStandardError = $stderr
  }
  if (-not $Visible) {
    $startInfo["WindowStyle"] = "Hidden"
  }
  $process = Start-Process @startInfo
  "Started LLM Studio backend PID=$($process.Id) at http://${HostName}:$Port"
  "stdout: $stdout"
  "stderr: $stderr"
} finally {
  Pop-Location
}
