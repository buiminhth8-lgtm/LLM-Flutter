$ErrorActionPreference = "Stop"

Write-Host "Python:"
python -c "import sys; print(sys.executable); print(sys.version)"

Write-Host "pip:"
python -m pip --version

python -m llm_studio.runtime.diagnostics
