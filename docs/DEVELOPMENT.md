# Development

Backend checks:

```powershell
python -m compileall llm_studio
python -m pytest
python -m ruff check llm_studio tests
python -m pip check
```

Flutter checks:

```powershell
.\scripts\flutter_analyze.ps1
.\scripts\flutter_test.ps1
.\scripts\flutter_build_windows.ps1
```

The Flutter tests use fake/local parsing paths only. They must not start the backend, download models, or use the GPU.
