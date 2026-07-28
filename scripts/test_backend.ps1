$ErrorActionPreference = "Stop"

python -m compileall llm_studio
python -m pytest

python -c "import ruff" 2>$null
if ($LASTEXITCODE -eq 0) {
  python -m ruff check llm_studio tests
} else {
  Write-Warning "ruff is not installed; skipping ruff check."
}

python -m pip check
python -m llm_studio.server --help

