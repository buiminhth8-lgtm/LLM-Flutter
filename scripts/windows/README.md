# LLM Studio Windows Scripts

These scripts are relative to the repository root and do not require hard-coded
absolute paths.

- `check_environment.ps1`: verifies Python, Flutter, writable data directory,
  and optional backend `/v1/health`.
- `start_backend.ps1`: starts `python -m llm_studio.server`.
- `start_flutter_desktop.ps1`: runs the Flutter Windows desktop app.
- `export_diagnostics.ps1`: exports a redacted diagnostics zip without model
  weights, API keys, cookies, or document bodies.
- `backup_data.ps1`: creates a local data backup excluding model/download
  weight directories.
- `restore_data.ps1`: restores a backup only when `-Confirm` is supplied.
