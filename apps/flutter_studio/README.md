# LLM Studio Flutter Client

This is the Windows Flutter desktop client for LLM-Studio. It owns the local Python/FastAPI backend lifecycle on desktop: when the app starts, it checks `/health` and starts the backend if it is not already running.

The backend is launched as a pure Python service with `python -m llm_studio.server`. The Flutter client does not use the old console-script executable or the old click-based CLI.

## Current Scope

Supported:

- First-run setup through `GET /v1/setup/status` and `POST /v1/setup/initialize`.
- API Key persistence with `shared_preferences`.
- Authenticated API calls using `Authorization: Bearer`, `X-User-ID`, and `X-API-Key`.
- Runtime status dashboard via `GET /v1/runtime`.
- Local model list via `GET /v1/models`.
- Model scan via `POST /v1/models/scan`.
- Model load via `POST /v1/models/{id}/load`.
- Current model via `GET /v1/models/current`.
- Model unload via `POST /v1/models/unload`.
- Non-streaming and SSE streaming chat via `POST /v1/chat/completions` using the selected model ID.
- Stop generation, clear history, and regenerate from the Chat page.
- Job Center on the Status page via `GET /v1/jobs`.
- Downloads page for starting small Hugging Face download jobs and viewing truthful task state.
- Minimal RAG query page.
- Adapter scan/load/activate/deactivate page.
- Experimental Benchmark page for current loaded model.
- Storage cleanup preview and execution page.
- Diagnostics export page with redaction explanation.
- Backend stdout/stderr log capture with secret redaction.
- Local/remote backend mode, backend restart, backend stop, and exit behavior settings.

Current limitations:

- Download pause is not a strict pause; cancel requests rely on backend cooperative cancellation and resumable cache.
- Benchmark remains experimental and is only a local development reference.
- LoRA merge is not exposed by default.
- RAG upload and document management remain minimal; backend jobs are surfaced through Job Center.
- `shared_preferences` is not a secure Windows key vault; move to Windows Credential Manager or secure storage in a later hardening pass.

## Developer Checks

From the repository root:

```powershell
.\scripts\flutter_analyze.ps1
.\scripts\flutter_test.ps1
.\scripts\flutter_build_windows.ps1
```

## Run on Windows

From the repository root:

```powershell
.\scripts\start_desktop.ps1
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
