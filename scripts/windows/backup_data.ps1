param(
  [string]$DataDir = "",
  [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
if ($DataDir.Trim().Length -eq 0) {
  $DataDir = Join-Path $repoRoot "data"
}
$arguments = @("scripts\backup_data.py", "--data-dir", $DataDir)
if ($OutputDir.Trim().Length -gt 0) {
  $arguments += @("--output-dir", $OutputDir)
}

Push-Location $repoRoot
try {
  & python @arguments
} finally {
  Pop-Location
}
