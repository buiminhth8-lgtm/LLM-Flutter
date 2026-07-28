# Flutter Client

The current first-class client is Flutter Windows desktop under `apps/flutter_studio`.

Implemented P3 surfaces:

- Status dashboard with runtime, GPU scheduler, capability chips, and Job Center.
- Models workspace for scan, refresh, load, unload, select-for-chat, and guarded delete.
- Chat with non-streaming mode, SSE streaming mode, stop generation, clear history, regenerate, current model display, and adapter display.
- Downloads page for creating small Hugging Face download jobs, viewing truthful progress fields, cancel, and retry.
- Minimal RAG query page.
- Adapter page for scan, load, activate, and deactivate.
- Experimental Benchmark page for the current loaded model.
- Storage page with cleanup preview before cleanup.
- Diagnostics page explaining redaction and exporting a diagnostic package.
- Settings page for local/remote backend mode, API settings, backend restart/stop, exit behavior, and redacted backend logs.

The client stores API keys in `shared_preferences` for now. This is acceptable for the current local desktop loop but is not a Windows credential vault.

Backend startup no longer uses a console-script executable or the historical click CLI. The desktop client starts the service with:

```powershell
python -m llm_studio.server --host 127.0.0.1 --port 8000
```
