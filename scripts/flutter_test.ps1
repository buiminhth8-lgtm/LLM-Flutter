$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  throw "Flutter SDK was not found in PATH."
}

Push-Location "$PSScriptRoot\..\apps\flutter_studio"
try {
  flutter test
} finally {
  Pop-Location
}
