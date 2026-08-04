# Phase 2 Codex 任务草案：ModelGateway Core

> 本文件是下一阶段（`feat/model-gateway-core`）的任务草案，**不是本阶段执行内容**。
> 当前分支 `chore/model-gateway-audit` 只产出审计与计划文档，不实现 Phase 2。

> 状态：Phase 2 已实现（`feat/model-gateway-core`，`llm_studio/model_gateway/`）。
> 本文档保留作为后续 WritingService 迁移（`refactor/writing-use-model-gateway`）
> 的参考。

## 任务标题

实现 Model Gateway 核心模块（local + fake Provider），不迁移业务调用点，
不接入在线 API。

## 目标

1. 新增 `llm_studio/model_gateway/` 模块。
2. 提供统一的 GenerateRequest / GenerateResult / StreamResult / ModelProfile /
   ModelProvider 接口与错误码。
3. 实现 LocalRuntimeProvider 与 FakeProvider 两个 Provider。
4. 实现 ModelGatewayService（profile 解析、provider 选择、调用、归一化）。
5. 新增单元测试；不迁移 WritingService / Runtime / 任何现有业务模块。
6. 不改数据库表、不改 Flutter UI、不新增在线 API 调用。

## 新建文件清单

```text
llm_studio/model_gateway/__init__.py
llm_studio/model_gateway/schemas.py
llm_studio/model_gateway/errors.py
llm_studio/model_gateway/provider_base.py
llm_studio/model_gateway/service.py
llm_studio/model_gateway/local_provider.py
llm_studio/model_gateway/fake_provider.py
tests/test_model_gateway_schemas.py
tests/test_model_gateway_service.py
tests/test_model_gateway_local_provider.py
tests/test_model_gateway_fake_provider.py
```

## 各文件职责

### schemas.py

- `GenerateRequest`（dataclass，frozen）：
  `model_id`、`prompt`、`temperature=0.8`、`top_p=0.9`、`max_tokens=2048`、
  `repetition_penalty=1.1`、`stop: list[str]`、`adapter_id: str | None`、
  `owner: str`、`extra: dict`。
- `Usage`（prompt_tokens / completion_tokens / total_tokens，默认 0）。
- `GenerateResult`（text、finish_reason、latency_ms、usage、provider、model_id、
  error_code、error_message）。
- `ModelProfile`（profile_id、provider、display_name、model_id、adapter_id、
  context_length、enabled、metadata）。

### errors.py

- 定义 `ModelGatewayError`（code + message + status_code）。
- 定义并导出以下 code 常量（不在 api/errors.py 全局注册，避免影响现有 API）：
  `MODEL_PROFILE_NOT_FOUND`、`MODEL_PROFILE_DISABLED`、
  `MODEL_PROVIDER_UNAVAILABLE`、`MODEL_PROVIDER_AUTH_FAILED`、
  `MODEL_PROVIDER_RATE_LIMITED`、`MODEL_PROVIDER_TIMEOUT`、
  `MODEL_PROVIDER_BAD_RESPONSE`、`MODEL_PROVIDER_STREAM_FAILED`、
  `MODEL_PROVIDER_PRIVACY_CONFIRM_REQUIRED`。

### provider_base.py

- `ModelProvider` Protocol / ABC：
  `provider_name`、`list_profiles() -> list[ModelProfile]`、
  `resolve_profile(profile_id) -> ModelProfile`、
  `async generate(request) -> GenerateResult`、
  `generate_stream(request) -> AsyncIterator[GenerateResult]`。
- 提供 `finish_reason` 归一化工具（stop/length/cancelled/error/unknown）。

### service.py

- `ModelGatewayService`：
  - 注册 providers（dict: name → provider）；
  - `list_profiles()`（聚合所有 provider）；
  - `generate(request)`：解析 profile → 选择 provider → 调用 → 归一化；
  - `generate_stream(request)`：同上，流式逐块 yield 归一化结果；
  - 校验：profile 不存在/禁用、provider 未注册、请求参数边界
    （temperature 0~2、top_p 0~1、max_tokens 1~32768、repetition_penalty 0.8~2）。
- 不持有任何 runner / 模型仓库引用；LocalRuntimeProvider 由外部注入依赖。

### local_provider.py

- `LocalRuntimeProvider`：
  - 构造参数：`resolve_runner`（复用 api_server 的 `_get_or_load_runner`）、
    `inference_scope`、`adapter_repository`、`profile_source`（可注入
    LocalModelRepository + AdapterRepository，用于生成 profile 列表）。
  - `generate`：等价于现有 `WritingRuntimeBridge.generate_text` 的行为
    （auto-load、adapter 加载/激活、并发 scope、错误映射为本地 code）。
  - `generate_stream`：等价于 `stream_text`（CancellationToken 取消、0 延迟
    语义由业务层处理）。
  - 本阶段只做薄封装，**不修改 `llm_studio/runner.py`**。

### fake_provider.py

- `FakeProvider`：可配置固定文本、流式块、usage、latency、错误；
  用于测试与后续开发。
- 提供一组默认 fake profiles。

### __init__.py

- 导出公共符号：GenerateRequest / GenerateResult / Usage / ModelProfile /
  ModelGatewayService / LocalRuntimeProvider / FakeProvider / ModelGatewayError。

## 单元测试要求

1. GenerateRequest 参数边界校验（temperature/top_p/max_tokens/repetition_penalty）。
2. FakeProvider 生成与流式正常路径、错误路径、usage 透传。
3. ModelGatewayService：
   - 未注册 provider → MODEL_PROVIDER_UNAVAILABLE；
   - profile 不存在 → MODEL_PROFILE_NOT_FOUND；
   - profile 禁用 → MODEL_PROFILE_DISABLED；
   - 流式逐块返回且结束事件含 finish_reason / usage。
4. LocalRuntimeProvider 用 fake resolve_runner / inference_scope 测试：
   - 正常生成与流式；
   - adapter 加载/激活路径（fake adapter_repository + fake runner）；
   - 错误映射为现有本地 code（MODEL_NOT_FOUND → 本地映射码）。
5. 所有测试不触碰数据库，不调用网络，不 import torch/llama_cpp。

## 验收标准

- `python -m compileall llm_studio` 通过。
- `python -m pytest tests/test_model_gateway_*.py` 全绿。
- `python -m pytest` 全量回归通过（现有 328+ 用例不受影响）。
- `python -m llm_studio.server --help` 正常。
- `flutter analyze` / `flutter test` 不受影响（本阶段不改 Flutter）。
- 未修改：`llm_studio/writing/service.py`、`llm_studio/runner.py`、
  `llm_studio/api_server.py` 的业务路径、数据库表、Flutter UI。

## 禁止项

- 不迁移 WritingService / EvaluationService / MemoryService /
  AdapterEvaluationService 到 gateway。
- 不新增 OpenAI / DeepSeek / 任何在线 Provider 实现。
- 不新增数据库表或迁移。
- 不修改 Flutter UI。
- 不删除或破坏 WritingRuntimeBridge 等旧接口。

## 提交建议

```powershell
git switch -c feat/model-gateway-core
git add llm_studio/model_gateway tests/test_model_gateway_*.py
git commit -m "feat: add model gateway core with local and fake providers"
```
