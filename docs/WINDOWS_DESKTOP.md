# Windows Desktop

Run the Windows client from the repository root:

```powershell
.\scripts\flutter_run_windows.ps1
```

For direct Flutter invocation:

```powershell
cd apps\flutter_studio
flutter run -d windows --dart-define="LLM_STUDIO_ROOT=D:\develop\LLM-Studio\LLM-Studio"
```

The client checks `/health`. When local backend mode and auto-start are enabled, it starts:

```powershell
.venv\Scripts\python.exe -m llm_studio.server
```

The client can also connect to a remote backend by switching Settings to remote backend mode.
