# Model Gateway Migration Plan

本文档是 Model Gateway 改造的迁移计划（规划稿，不是实现）。本阶段不新增
ModelGateway 代码、不新增数据库迁移、不改 Flutter UI、不接入在线 API。
后续阶段由 Codex 按本计划分步执行，每步独立验收。

## 1. 改造目标

- 为 Writing / Evaluation / Memory / Adapter Evaluation（以及未来 chat / rag）
  提供统一的模型调用入口（Model Gateway）。
- 引入 Provider 抽象：本地 Runtime 是第一个 Provider（LocalRuntimeProvider），
  未来可追加 OpenAI 兼容 Provider（含 DeepSeek Preset）。
- 统一 GenerateRequest / GenerateResult / 流式结果 / 错误码 / usage 语义。
- 保持现有业务行为与旧接口兼容，不一次性重构全项目。

## 2. 目标架构

```text
Flutter UI
    ↓
Novel Studio 业务模块（WritingService / EvaluationService / MemoryService /
                         AdapterEvaluationService / 未来 chat / rag）
    ↓
Model Gateway（service：解析 ModelProfile → 选择 Provider → 调用 → 归一化结果）
    ↓
Providers（LocalRuntimeProvider / FakeProvider / OpenAICompatibleProvider / DeepSeek）
    ↓
本地 Runner / 在线 API
```

业务模块不再直接持有 runner 或“本地模型 id”语义；它们只依赖 Model Gateway
接口。旧接口（如 WritingRuntimeBridge）保留为兼容层，可逐步删除。

## 3. 核心设计原则

1. 接口先行：先定义 GenerateRequest / GenerateResult / ModelProfile / Provider
   接口，再迁移调用点。
2. 向后兼容：不删除旧接口；迁移期间新旧路径并存，feature flag 或注入选择。
3. 本地优先：LocalRuntimeProvider 行为与现状完全一致（含 auto-load、adapter、
   concurrency、GPU scheduler），保证本地 Novel 生成功能不受影响。
4. 无 Provider 硬编码：业务层不 import 具体 Provider。
5. usage 为可选字段：本地无真实 usage 时保持估算，在线 Provider 填充真实值。
6. 错误码统一前缀：MODEL_PROVIDER_* / MODEL_PROFILE_*，并兼容映射旧码。
7. 隐私与密钥：在线 API Key 不出现在日志/数据库/诊断包中。

## 4. ModelGateway 目标接口草案

以下为计划接口（伪代码，Phase 2 实现时可调整，不做为实现承诺）。

### 4.1 GenerateRequest

```python
@dataclass(frozen=True)
class GenerateRequest:
    model_id: str            # ModelProfile.id 或本地 model id
    prompt: str
    temperature: float = 0.8
    top_p: float = 0.9
    max_tokens: int = 2048
    repetition_penalty: float = 1.1
    stop: list[str] = field(default_factory=list)
    adapter_id: str | None = None      # 仅本地 Provider 使用
    owner: str = ""                    # 请求方标识（并发/取消/日志）
    extra: dict[str, Any] = field(default_factory=dict)
```

### 4.2 GenerateResult

```python
@dataclass(frozen=True)
class GenerateResult:
    text: str
    finish_reason: str                   # stop | length | cancelled | error | unknown
    latency_ms: int | None = None
    usage: Usage | None = None           # 可选：真实 usage
    provider: str = "local"              # local | fake | openai_compatible | deepseek
    model_id: str = ""
    error_code: str | None = None
    error_message: str | None = None

@dataclass(frozen=True)
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
```

### 4.3 StreamGenerateResult

```python
class StreamGenerateResult(Protocol):
    def __aiter__(self) -> AsyncIterator[str]: ...
    def cancel(self) -> None: ...
```

Gateway 提供 `generate_stream(request) -> AsyncIterator[GenerateResult]`，
业务层可逐块消费并在结束时获得归一化结果（含 finish_reason / usage / latency）。

### 4.4 ModelProfile

```python
@dataclass(frozen=True)
class ModelProfile:
    profile_id: str              # 全局唯一（如 local:qwen2.5-1.5b / deepseek:chat）
    provider: str                # local | fake | openai_compatible | deepseek
    display_name: str
    model_id: str                # provider 内模型标识（本地仓库 id / 在线模型名）
    adapter_id: str | None = None
    context_length: int | None = None
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 4.5 ModelProvider

```python
class ModelProvider(Protocol):
    provider_name: str
    async def generate(self, request: GenerateRequest) -> GenerateResult: ...
    def generate_stream(
        self, request: GenerateRequest
    ) -> AsyncIterator[GenerateResult]: ...
    def list_profiles(self) -> list[ModelProfile]: ...
    def resolve_profile(self, profile_id: str) -> ModelProfile: ...
```

## 5. Provider 规划

### 5.1 LocalRuntimeProvider

- 包装现有 `_get_or_load_runner` + `inference_scope`（`llm_studio/api_server.py`），
  复用 `llm_studio/runner.py` 的 BaseRunner 与 `models/selection.py`。
- 支持 adapter_id（本地 PEFT）；保留 auto-load 与 GPU scheduler。
- 无真实 usage 时返回估算或 None；finish_reason 由 gateway 归一化。
- Profile 来源：LocalModelRepository 扫描结果（每个 READY 本地模型一个 profile；
  可选为每个已注册 Adapter 生成 base+adapter 组合 profile）。

### 5.2 FakeProvider

- 测试专用：固定文本 / 可注入错误、流式块、usage、latency。
- 替换现有 `FakeRuntimeBridge` 测试模式
  （`tests/test_writing_service.py::FakeRuntimeBridge`）。

### 5.3 OpenAICompatibleProvider

- 通用 OpenAI 兼容 HTTP 客户端（chat/completions，stream 支持）。
- API Key 由 Flutter 端保存并在请求时传入；后端仅透传，不落库。
- 错误映射：HTTP 401/429/5xx/timeout → MODEL_PROVIDER_* 错误码。

### 5.4 DeepSeek Preset

- 在 OpenAICompatibleProvider 之上配置 DeepSeek 预设
  （base_url、默认模型、参数范围、上下文长度）。
- 仅作为配置/预设，不写死 provider 专用代码。

## 6. 分阶段迁移计划

### Phase 1: Audit（本阶段，已完成）

- 输出本审计报告与迁移计划、Phase 2 任务草案。只改 docs。

### Phase 2: ModelGateway Core（已实现）

- 已新增 `llm_studio/model_gateway/` 模块：schemas.py、provider_base.py、
  service.py、errors.py、fake_provider.py、local_provider.py、routing.py。
- 已新增单元测试（`tests/test_model_gateway_*.py`）。
- 未迁移任何业务调用点；未接入在线 API；未新增数据库表。

### Phase 3: WritingService 迁移（已实现）

- WritingRuntimeBridge 对外接口保持不变，内部经 ModelGatewayService 路由：
  `WritingService -> WritingRuntimeBridge -> ModelGatewayService ->
  LocalRuntimeProvider -> 现有 Runtime`。
- 默认 provider 仍为 local_runtime；model_id / adapter_id / generation_params
  透传不变；streaming、target_length、warnings、finish_reason、latency 与
  generation_records 行为保持兼容。
- 未接入任何在线 Provider；generation_records 字段未改。
- 验收：/v1/writing/generate 与 /v1/writing/stream 行为不变，测试全绿。

### Phase 4: Model Profiles

- 新增 ModelProfile 解析与持久化（本地 profile 自动生成 + 用户自定义
  profile 表或配置）。
- Flutter 模型选择改为基于 profile 列表。

### Phase 5: OpenAI-Compatible Provider

- 实现 OpenAICompatibleProvider + 配置（base_url / api_key 引用 / 模型）。
- 不默认启用；通过配置或 profile 开关启用。

### Phase 6: DeepSeek Preset

- 在配置中增加 DeepSeek 预设（不写死 provider 代码）。

### Phase 7: Writing Provider Switch

- Writing 页面支持本地/在线模型切换（profile 选择），其余模块暂保持本地。

### Phase 8: Privacy / Usage / Diagnostics

- usage 归一化入库；在线 API Key 生命周期与脱敏审计；诊断包字段扩展。

### Phase 9: Evaluation Cloud Judge

- Evaluation 新增 cloud judge 评估器（复用 gateway），保留本地 judge。

### Phase 10: Local vs Cloud Comparison

- 支持同一 prompt 的本地/在线对比（可复用 Adapter Evaluation 对比 UI 模式）。

## 7. 数据库变更建议

本阶段不改数据库。未来建议（Phase 3/4 时评估）：

- `generation_records`：新增 `provider`、`usage_json`（prompt/completion/total
  tokens）、保留估算字段以兼容历史数据。
- 新增 `model_profiles` 表（或复用配置）：profile_id、provider、model_id、
  adapter_id、context_length、enabled、metadata。
- 新增 `provider_credentials` 引用表（仅存引用标识，不存密钥本身）。

## 8. API 变更建议

本阶段不改 API。未来建议：

- `POST /v1/writing/generate` / `stream`：`model_id` 语义扩展为接受
  ModelProfile id（本地 id 兼容）；
- 新增 `GET /v1/model-profiles`、`GET /v1/model-providers`；
- 错误响应新增 MODEL_PROVIDER_* / MODEL_PROFILE_* code；
- 保持旧 code 与 HTTP 状态映射不变，避免破坏 Flutter 错误映射。

## 9. Flutter UI 变更建议

本阶段不改 UI。未来建议：

- 模型选择器改为 ModelProfile 选择（显示 provider 标记、上下文长度）；
- 生成参数面板增加流式开关与 usage 展示（tokens / latency）；
- Settings 增加 Provider 配置入口（base_url、API Key 引用、DeepSeek 预设开关）；
- 错误提示支持 MODEL_PROVIDER_* 中文映射
  （扩展 `apps/flutter_studio/lib/core/errors/error_mapper.dart`）。

## 10. 隐私和密钥策略

- 在线 Provider API Key：Flutter 端本地保存（沿用 shared_preferences 模式），
  每次请求透传；后端不落库、不写日志、不出现在 generation_records。
- 诊断包：继续使用 `llm_studio/diagnostics/redaction.py` 脱敏，新增
  provider 配置导出时去除密钥。
- 日志：redact_sensitive_text 扩展识别 provider key 常见前缀。

## 11. 错误码规划

新增（Phase 2 先在 model_gateway/errors.py 定义，业务迁移时接入）：

```text
MODEL_PROVIDER_UNAVAILABLE
MODEL_PROVIDER_AUTH_FAILED
MODEL_PROVIDER_RATE_LIMITED
MODEL_PROVIDER_TIMEOUT
MODEL_PROVIDER_BAD_RESPONSE
MODEL_PROVIDER_STREAM_FAILED
MODEL_PROVIDER_PRIVACY_CONFIRM_REQUIRED
MODEL_PROFILE_NOT_FOUND
MODEL_PROFILE_DISABLED
```

映射规则：

- 本地 Provider 失败 → 复用现有 WRITING_MODEL_NOT_FOUND / WRITING_MODEL_NOT_LOADED /
  WRITING_GENERATION_FAILED / WRITING_STREAM_FAILED；
- 在线 Provider 失败 → MODEL_PROVIDER_*，并在 Flutter error_mapper 增加中文文案。

## 12. 测试计划

- Phase 2：model_gateway 单元测试（fake provider、参数归一化、错误映射、
  usage 透传、流式取消）。
- Phase 3：writing 回归（复用现有 fake bridge 测试，改为注入 fake provider）；
  API 契约测试保持稳定。
- 每个 Phase：`python -m compileall llm_studio`、`python -m pytest`、
  `flutter analyze`、`flutter test`。

## 13. 风险和回滚方案

风险：

- 迁移 WritingService 可能影响本地生成行为（长度控制、流式取消、adapter）。
- 在线 Provider 引入网络/密钥风险。
- generation_records 字段变化影响历史数据展示。

回滚：

- 每个 Phase 独立提交；保留旧接口（bridge）作为 fallback；
- 若 Phase 3 异常，可通过配置开关退回 bridge 路径；
- 数据库变更均加可逆迁移（新增列默认值兼容旧数据）。

## 14. MVP 范围

MVP = Phase 2 + Phase 3：

- 建立 model_gateway 核心（local + fake provider）；
- WritingService 迁移到 gateway，本地行为完全一致；
- 不接入在线 API、不新增 UI、不引入新表（如无必要）。

## 15. 验收标准

- `python -m pytest` 全绿（含新增 model_gateway 测试与 writing 回归）。
- `/v1/writing/generate`、`/v1/writing/stream` 行为与迁移前一致
  （文本、warnings、finish_reason、save_to_chapter、cancel）。
- LocalRuntimeProvider 覆盖现状所有能力（auto-load、adapter、并发、GPU scheduler）。
- 旧 WritingRuntimeBridge 接口保留且可由配置切换回退。
- 未引入在线 Provider 代码；密钥策略符合第 10 节。
- Flutter analyze / test 全绿；无未计划 UI 改动。
