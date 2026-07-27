$ErrorActionPreference = "Stop"

Write-Host "当前项目为 Gradio/FastAPI Web 应用，桌面启动器会打开 Web UI。"
& "$PSScriptRoot\start_web.ps1"
