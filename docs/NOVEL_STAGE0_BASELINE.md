# Novel Studio Stage 0 Baseline

## 当前验证命令和结果

- `python -m compileall llm_studio`: passed.
- `python -m pytest --basetemp .pytest_tmp`: 142 passed, 1 warning.
- `python -m llm_studio.server --help`: passed.
- `python -m ruff check llm_studio tests`: passed.
- `flutter analyze`: passed.
- `flutter test`: passed, 58 tests.
- Python: 3.12.7.
- OS: Microsoft Windows 11 专业工作站版.

## 当前后端入口

- Service entrypoint: `python -m llm_studio.server`.
- FastAPI app export: `llm_studio.api_server:app`.
- Router package: `llm_studio/api/routers/`.
- Existing split routers: capabilities, diagnostics, downloads, jobs, storage.

## 当前 Flutter 入口

- Desktop app shell: `apps/flutter_studio/lib/app/app_shell.dart`.
- Primary settings surface: `apps/flutter_studio/lib/features/settings/settings_page.dart`.
- Shared API client: `apps/flutter_studio/lib/core/api/api_client.dart`.
- Shared UI components: `apps/flutter_studio/lib/core/ui/`.

## 可复用模块清单

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

## 不可触碰模块清单

1. Runtime / Runner 不在阶段 0 重构。
2. ModelScope 下载逻辑不在阶段 0 重写。
3. 认证和 API Key 恢复不在阶段 0 扩展。
4. LoRA 训练不在阶段 0 实现。

## 后续阶段依赖

- Stage 1 must define Novel data boundaries before adding repositories.
- Stage 1 must add explicit API contracts before Flutter calls.
- Stage 1 must keep existing RBAC, error.code, and path safety conventions.
- Stage 1 must use existing JobQueue for background work.

## 已知风险

- Novel-specific workflows will touch persistence, prompts, generation, and
  possibly RAG memory. Each area needs separate tests before exposure.
- Capabilities must remain truthful; placeholders must not be shown as
  available features.
- Long-form generation must not bypass GPU Scheduler or loaded-model policy.

## 阶段 1 开发前置条件

- Confirm data model and migration strategy.
- Define `/v1/novels` API contract before implementation.
- Define RBAC requirements for project and corpus access.
- Define Flutter navigation exposure rules based on feature flag and
  capabilities.
