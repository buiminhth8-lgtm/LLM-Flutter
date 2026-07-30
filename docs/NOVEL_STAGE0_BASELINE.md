# Novel Studio Stage 0 Baseline

Stage 0 prepared the engineering entry point for Novel Studio without adding
business APIs or data tables. Stage 1 now builds on that foundation.

## Stage 0 Verification

- `python -m compileall llm_studio`: passed.
- `python -m pytest --basetemp .pytest_tmp`: passed.
- `python -m llm_studio.server --help`: passed.
- `python -m ruff check llm_studio tests`: passed.
- `flutter analyze`: passed.
- `flutter test`: passed.

## Backend Entry

- Service entrypoint: `python -m llm_studio.server`.
- FastAPI export: `llm_studio.api_server:app`.
- Router package: `llm_studio/api/routers/`.

## Flutter Entry

- App shell: `apps/flutter_studio/lib/app/app_shell.dart`.
- Settings: `apps/flutter_studio/lib/features/settings/settings_page.dart`.
- Shared API client: `apps/flutter_studio/lib/core/api/api_client.dart`.
- Shared UI components: `apps/flutter_studio/lib/core/ui/`.

## Reusable Modules

- `llm_studio/models/`
- `llm_studio/runtime/`
- `llm_studio/adapters/`
- `llm_studio/jobs/`
- `llm_studio/storage/`
- `llm_studio/downloads/`
- `llm_studio/diagnostics/`
- `llm_studio/api/errors.py`
- `llm_studio/api/routers/`
- `apps/flutter_studio/lib/core/api/`
- `apps/flutter_studio/lib/core/ui/`

## No-Touch Modules For Stage 0

- Runtime / Runner.
- ModelScope download logic.
- Authentication recovery.
- LoRA / QLoRA training.

## Stage 1 Prerequisites

- Define Novel data model and migrations.
- Define `/v1/novels` API contract.
- Define initial RBAC policy.
- Gate Flutter navigation with capabilities and feature flag state.

Stage 1 implementation details are documented in
[NOVEL_STAGE1_FOUNDATION.md](NOVEL_STAGE1_FOUNDATION.md).
