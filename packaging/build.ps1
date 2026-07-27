$ErrorActionPreference = "Stop"

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
  throw "未找到 .venv。请先创建 Python 3.12 虚拟环境。"
}

.\.venv\Scripts\python.exe -m pip show pyinstaller | Out-Null
if ($LASTEXITCODE -ne 0) {
  throw "未安装 PyInstaller。请明确安装后再执行打包。"
}

.\.venv\Scripts\python.exe -m PyInstaller packaging\llm_studio.spec
