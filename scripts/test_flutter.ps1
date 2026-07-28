$ErrorActionPreference = "Stop"

if (-not (Get-Command flutter -ErrorAction SilentlyContinue)) {
  throw "Flutter SDK was not found on PATH. Install Flutter and enable Windows desktop before running this script."
}

Push-Location "apps\flutter_studio"
try {
  flutter pub get
  flutter analyze
  flutter test
} finally {
  Pop-Location
}

