param(
  [switch]$Release
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$flutterRoot = Join-Path $repoRoot "apps\flutter_studio"

Push-Location $flutterRoot
try {
  if ($Release) {
    flutter run -d windows --release
  } else {
    flutter run -d windows
  }
} finally {
  Pop-Location
}
