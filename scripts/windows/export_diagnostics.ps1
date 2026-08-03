param(
  [string]$Output = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$arguments = @("-m", "llm_studio.diagnostics.export")
if ($Output.Trim().Length -gt 0) {
  $arguments += @("--output", $Output)
}

Push-Location $repoRoot
try {
  & python @arguments
} finally {
  Pop-Location
}
