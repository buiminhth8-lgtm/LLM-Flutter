$ErrorActionPreference = "Stop"

$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location (Join-Path $projectRoot "apps\flutter_studio")

$flutter = (Get-Command flutter -ErrorAction SilentlyContinue).Source
if (-not $flutter) { throw "Flutter SDK was not found. Add flutter\bin to PATH." }

Write-Host "Starting LLM-Studio Flutter desktop client. The app will start the local API service."
& flutter run -d windows --dart-define="LLM_STUDIO_ROOT=$projectRoot" --dart-define="LLM_STUDIO_API_BASE=http://127.0.0.1:8000"
