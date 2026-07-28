# Legacy Architecture Cleanup Audit

Date: 2026-07-28
Branch: `cleanup-legacy-architecture`

## Scope

This cleanup removes leftovers from the pre-Flutter and pre-service startup architecture while preserving the P0/P1/P2 backend and Flutter desktop workflows.

## Findings And Decisions

| Area | Finding | References | Decision | Verification |
| --- | --- | --- | --- | --- |
| CLI startup | `llm_studio/cli.py` was a no-click compatibility wrapper after the service migration. No production module imports it. | `rg "from llm_studio.cli|llm_studio.cli|cli.py"` | Delete. The service entrypoint is `llm_studio.server`. | `python -m llm_studio.server --help`, `tests/test_server_entrypoint.py` |
| Console script | `[project.scripts]` and `llm-studio` console script were already removed. | `pyproject.toml`, `requirements/base.txt` | Keep removed. Existing `llm-studio.exe` in old virtualenvs is a stale generated file, not a project dependency. | `rg "project.scripts|llm-studio =" pyproject.toml requirements` |
| `click` dependency | No production code imports `click`; tests only assert the server import does not require it. | `tests/test_server_entrypoint.py` | Keep `click` out of dependencies. | `rg "import click|click" pyproject.toml requirements llm_studio tests` |
| Old model downloader | `llm_studio/downloader.py` provided the old `models_dir` / Hugging Face download path. No production or test code imports it. | `rg "ModelDownloader|llm_studio.downloader"` | Delete. Model facts now come from `LocalModelRepository`, `ModelScanner`, and `models.root_dir`. | `rg "ModelDownloader|list_local_models" llm_studio tests apps` |
| Legacy model directory | Top-level `models_dir` in `config.yaml` pointed at `./models`. | `config.yaml`, `llm_studio/config.py` | Remove from default config. Keep load-time migration for old user configs with top-level `models_dir`. | `tests/test_encoding_and_config.py` |
| Encoding report | `tools/encoding_conversion_report.json` was a one-time generated audit report and referenced deleted legacy files. | `tools/encoding_conversion_report.json` | Delete generated report. Keep `tools/convert_repository_to_utf8.py`. | UTF-8 tests and compile checks |
| Startup scripts | Current scripts start Flutter or `python -m llm_studio.server`; no script launches `llm-studio.exe` or `llm_studio.cli`. | `scripts/*.ps1` | Keep current scripts. | `rg "llm-studio|llm_studio.cli" scripts` |
| Upload safety | `file.filename` and `file.read` only appear in `llm_studio/security/uploads.py`; filename is sanitized and reads are chunked. | `llm_studio/security/uploads.py` | Keep. Not a legacy unsafe path. | Upload security tests |
| `NotImplemented` | Abstract runner methods and explicit `JobNotImplementedError` for unimplemented LoRA merge executor remain intentional. | `llm_studio/runner.py`, `llm_studio/jobs/exceptions.py`, `llm_studio/api_server.py` | Keep. These are capability/status boundaries, not stale startup code. | Capability and job tests |
| Flutter backend launcher | Flutter starts `python -m llm_studio.server` and captures redacted stdout/stderr. | `apps/flutter_studio/lib/core/backend/backend_service_io.dart` | Keep. | `apps/flutter_studio/test/backend_service_test.dart` |

## Deleted

- `llm_studio/cli.py`
- `llm_studio/downloader.py`
- `tools/encoding_conversion_report.json`

## Preserved Compatibility

- Legacy user configs containing top-level `models_dir` still load. If no `models.root_dir` is present, `models_dir` is mapped to `models.root_dir` during config loading.
- Documentation may mention stale `llm-studio.exe` only as a deprecated virtualenv artifact.
- Flutter tests keep negative assertions to prevent returning to `llm-studio.exe` or `llm_studio.cli`.

## Validation Commands

```powershell
python -m compileall llm_studio
python -m pytest
python -m ruff check llm_studio tests
python -m pip check
python -m llm_studio.server --help
cd apps\flutter_studio
flutter analyze
flutter test
flutter build windows
```

## Latest Validation Results

- `python -m compileall llm_studio`: passed.
- `python -m pytest --basetemp .tmp\pytest`: passed, 68 tests, 1 warning. The default Temp directory was not readable in this environment.
- `python -m ruff check llm_studio tests`: passed.
- `python -m pip check`: passed.
- `python -m llm_studio.server --help`: passed.
- `flutter analyze`: passed.
- `flutter test`: passed, 12 tests.
- `flutter build windows`: passed.
- `/health` smoke test: not passed in the current shell because `uvicorn` is missing from the active `python` environment. This cleanup did not install dependencies automatically.

## Latest Residual Scan Results

- `llm-studio.exe`, `llm_studio.cli`, `import click`, and `project.scripts`: no production code hits. Remaining hits are deprecated documentation notes and Flutter negative regression assertions.
- `ModelDownloader`, `list_local_models`, and `model=auto`: no source hits under `llm_studio`, `apps/flutter_studio`, or `tests`.
- Upload scan hits are limited to FastAPI upload endpoints and `llm_studio/security/uploads.py`; file names are sanitized and file reads are chunked.
- `NotImplemented` hits are intentional abstract runner methods, explicit job error typing, and tests that assert those boundaries.
