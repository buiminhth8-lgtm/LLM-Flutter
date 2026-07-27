$ErrorActionPreference = "Stop"

Write-Host "Starting LLM-Studio Flutter desktop client. Legacy Gradio UI remains available via scripts\start_web.ps1."
& "$PSScriptRoot\start_flutter.ps1"
