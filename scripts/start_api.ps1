$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  throw "未找到 .venv。请先运行 scripts\setup_windows_python312.ps1。"
}

$python = ".\.venv\Scripts\python.exe"
& $python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if ($LASTEXITCODE -ne 0) { throw "需要 Python 3.12 x64 虚拟环境。" }

& $python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() else 1)"
if ($LASTEXITCODE -ne 0) { throw "需要 CUDA 版 PyTorch，不能使用 CPU 版 torch。" }

& $python -m llm_studio.cli serve
