# LLM Studio Flutter Client

This is the Flutter desktop client for LLM-Studio.
It owns the local Python/FastAPI backend lifecycle on desktop: when the app starts, it checks `/health` and starts the backend if it is not already running.

## Current scope

- Runtime status dashboard via `GET /v1/runtime`
- Local model list via `GET /v1/models`
- Non-streaming chat via `POST /v1/chat/completions`
- Configurable API base URL
- Runtime-only API key entry through Settings. Keys are sent as `X-User-ID` and `X-API-Key` headers and are not persisted by the Flutter client.

## Run on Windows

From the repository root:

```powershell
.\scripts\start_desktop.ps1
```

The Flutter app locates the repository root through `LLM_STUDIO_ROOT` and starts:

```text
.venv\Scripts\python.exe -m llm_studio.cli serve --host 127.0.0.1 --port 8000
```

For direct Flutter development, pass the repository root explicitly:

```powershell
cd apps\flutter_studio
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

If your Python environment is not in `.venv`, also pass the Python executable:

```powershell
flutter run -d windows `
  --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio" `
  --dart-define="LLM_STUDIO_PYTHON=D:\path\to\python.exe"
```

If the app reports a missing Python executable, create the project virtual environment first:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\scripts\install_windows_cuda.ps1
.\scripts\install_base.ps1
```

## Next UI milestones

- Streaming SSE chat
- Model download and job progress pages
- RAG management
- LoRA management
- Benchmark reports
- Config import/export and diagnostics export
