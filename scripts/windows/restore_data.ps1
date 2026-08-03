param(
  [Parameter(Mandatory=$true)][string]$Backup,
  [string]$DataDir = "",
  [switch]$Confirm
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
if ($DataDir.Trim().Length -eq 0) {
  $DataDir = Join-Path $repoRoot "data"
}
if (-not $Confirm) {
  throw "Restore requires -Confirm. This may overwrite files under the selected data directory."
}

Push-Location $repoRoot
try {
  & python scripts\restore_data.py --backup $Backup --data-dir $DataDir --confirm
} finally {
  Pop-Location
}
