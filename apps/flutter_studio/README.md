# LLM Studio Flutter Client

This is the first-stage Flutter replacement for the legacy Gradio UI.
It keeps the Python/FastAPI backend as the local runtime and talks to it over REST.

## Current scope

- Runtime status dashboard via `GET /v1/runtime`
- Local model list via `GET /v1/models`
- Non-streaming chat via `POST /v1/chat/completions`
- Configurable API base URL

The legacy Gradio UI is still available through `scripts/start_web.ps1` while this client is expanded.

## Run on Windows

From the repository root:

```powershell
.\scripts\start_desktop.ps1
```

Or run the Flutter client directly after starting the API:

```powershell
cd apps\flutter_studio
flutter run -d windows --dart-define="LLM_STUDIO_API_BASE=http://127.0.0.1:8000"
```

## Run as Flutter Web

Start the API first, then run:

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
