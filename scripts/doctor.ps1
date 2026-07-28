$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  throw "未找到 .venv。请先运行 scripts\setup_windows_python312.ps1。"
}

$python = ".\.venv\Scripts\python.exe"
& $python -m llm_studio.runtime.diagnostics
& $python -m llm_studio.server --help
