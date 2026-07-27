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

## Run as Flutter Web

Flutter Web does not start the backend process. Start the API separately for web development, then run:

```powershell
cd apps\flutter_studio
flutter run -d chrome --web-port 5000 --dart-define="LLM_STUDIO_API_BASE=http://127.0.0.1:8000"
```

The API CORS defaults include common Flutter dev origins on ports `5000` and `8080`.

## Next UI milestones

- Streaming SSE chat
- Model download and job progress pages
- RAG management
- LoRA management
- Benchmark reports
- Config import/export and diagnostics export
