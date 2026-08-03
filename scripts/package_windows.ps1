param(
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$flutterRoot = Join-Path $repoRoot "apps\flutter_studio"
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$releaseRoot = Join-Path $repoRoot "dist\windows\llm-studio-$stamp"
$bundleSource = Join-Path $flutterRoot "build\windows\x64\runner\Release"

if (-not $SkipBuild) {
  Push-Location $flutterRoot
  try {
    flutter build windows --release
  } finally {
    Pop-Location
  }
}

if (-not (Test-Path -LiteralPath $bundleSource)) {
  throw "Windows release bundle not found: $bundleSource"
}

New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
Copy-Item -LiteralPath $bundleSource -Destination (Join-Path $releaseRoot "app") -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot "scripts\windows") -Destination (Join-Path $releaseRoot "scripts") -Recurse
Copy-Item -LiteralPath (Join-Path $repoRoot "docs\WINDOWS_RELEASE_GUIDE.md") -Destination $releaseRoot -ErrorAction SilentlyContinue
Copy-Item -LiteralPath (Join-Path $repoRoot "docs\RELEASE_CHECKLIST.md") -Destination $releaseRoot -ErrorAction SilentlyContinue

$manifest = [pscustomobject]@{
  app = "LLM Studio"
  platform = "windows"
  created_at = (Get-Date).ToUniversalTime().ToString("o")
  contains_model_weights = $false
  contains_api_keys = $false
  bundle = "app"
}
$manifest | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $releaseRoot "release-manifest.json") -Encoding UTF8

"Release package prepared: $releaseRoot"
