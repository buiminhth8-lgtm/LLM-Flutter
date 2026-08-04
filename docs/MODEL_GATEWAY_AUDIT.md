# Model Gateway Audit

本文档是 Model Gateway 改造第一步的审计结果。只描述现状，不包含实现代码，
不提出立即重构全项目的建议。所有结论均标注对应源码文件路径；未找到的内容
明确写“未发现”。

## 1. 审计目标

- 审计当前 llm-studio 中所有模型调用入口。
- 梳理 Writing / Evaluation / Memory / Adapter Evaluation 如何调用本地 Runtime。
- 梳理 model_id、adapter_id、generation_params、streaming、usage、error code 的传递方式。
- 输出 Model Gateway 改造方案（见 `docs/MODEL_GATEWAY_MIGRATION_PLAN.md`）。
- 本阶段不改业务逻辑、不接入在线 Provider、不改数据库表。

## 2. 当前模型调用总览

### 2.1 唯一的模型运行时

所有本地文本生成都经由 `llm_studio/runner.py` 中的 `BaseRunner`：

- `TransformersRunner`（HuggingFace Transformers）：`llm_studio/runner.py`（约 110 行起）
- `GGUFRunner`（llama-cpp-python）：`llm_studio/runner.py`（约 300 行起）
- 工厂 `create_runner(model_path, config)`：`llm_studio/runner.py`（约 370 行起）

Runner 实例按 model_path 缓存在 `llm_studio/api_server.py` 的模块级
`_runners`；`_runner_model_ids` 记录 path → model_id；`_current_model_id`
记录“当前模型”（单值，不区分请求方）。

### 2.2 统一的调用桥接：WritingRuntimeBridge

Novel Studio 各模块（Writing / Evaluation / Memory / Adapter Evaluation）
共用**同一个** `WritingRuntimeBridge` 实例，装配于 `llm_studio/api_server.py`
（约 652 行）：

```text
WritingRuntimeBridge(
    resolve_runner=_get_or_load_runner,
    inference_scope=_writing_inference_scope,
    adapter_repository=_adapter_repository,
)
```

该桥接位于 `llm_studio/writing/runtime_bridge.py`，封装：

- `_runner()`：解析并自动加载 runner（`_get_or_load_runner`，见
  `llm_studio/api_server.py` 约 568 行），加载/激活/停用 Adapter
  （`runner.load_adapter` / `activate_adapter` / `deactivate_adapter`）。
- `generate_text()`：非流式生成，返回 `RuntimeTextResult{text, finish_reason, latency_ms}`
  （`llm_studio/writing/entities.py`）；`finish_reason` 固定为 `"stop"`。
- `stream_text()`：流式生成，yield 文本块；`finish_reason` 不返回。
- 并发控制：`inference_scope`（`_writing_inference_scope`，`llm_studio/api_server.py`
  约 637 行）套用 `concurrency.inference` + `gpu_scheduler`（INFERENCE 任务）。

### 2.3 调用方清单

| 调用方 | 调用方式 | 文件 |
| --- | --- | --- |
| WritingService.generate | bridge.generate_text | `llm_studio/writing/service.py` |
| WritingService.stream_generate | bridge.stream_text | `llm_studio/writing/service.py` |
| EvaluationService → LocalModelJudgeEvaluator | bridge.generate_text | `llm_studio/evaluation/evaluators/local_model_judge.py` |
| MemoryService.generate_chapter_summary | writing_service.runtime_bridge.generate_text | `llm_studio/memory/service.py`（约 345 行） |
| AdapterEvaluationService → AdapterComparisonRunner | bridge.generate_text | `llm_studio/adapter_evaluation/comparison_runner.py` |
| `/v1/chat/completions`（OpenAI 兼容聊天） | 直接 runner.generate / generate_stream | `llm_studio/api_server.py`（约 1021 行起） |
| `/v1/rag/query`（指定 model 时生成回答） | 直接 runner.generate | `llm_studio/api_server.py`（约 1280 行起） |
| `/v1/vision/analyze` | VisionRunner（独立视觉运行器） | `llm_studio/api_server.py`（约 1325 行起） |
| `/v1/benchmarks` | BenchmarkRunner(create_runner) | `llm_studio/api_server.py`（约 974 行） |
| Adapter 加载/合并 | runner + AdapterManager | `llm_studio/adapters/manager.py`、`llm_studio/adapters/merge.py` |

结论：

1. 直接或间接调用 Runtime 的后端模块：writing、evaluation、memory、
   adapter_evaluation、chat（/v1/chat/completions）、rag（可选回答生成）、
   vision、benchmarks、adapters。
2. 通过 WritingRuntimeBridge 调用 Runtime 的模块：writing、evaluation
   （local_model_judge）、memory（章节摘要）、adapter_evaluation
   （comparison_runner）。
3. 直接持有 model_id 的模块：writing（请求字段）、memory（摘要请求字段）、
   evaluation（evaluator_config.local_model_id）、adapter_evaluation
   （session.base_model_id）、chat/rag/benchmarks/vision（请求字段）。
4. 直接持有 adapter_id 的模块：writing（请求字段）、adapter_evaluation
   （session.adapter_id）；evaluation 与 memory 摘要均不使用 adapter。
5. 支持 streaming 的模块：writing（/v1/writing/stream）、chat
   （/v1/chat/completions stream）。
6. 只支持非 streaming 的模块：evaluation local judge、memory 摘要、
   adapter_evaluation 对比、rag 回答、benchmarks。
7. 保存 generation_records 的模块：writing（`generation_records` 表，
   `llm_studio/writing/repository.py`、`migrations.py`）。
8. 记录 tokens / latency / finish_reason 的模块：writing 记录估算 token
   （input/output_token_estimate）、latency_ms（非流式）、finish_reason；
   adapter_evaluation 记录 output_token_estimate、latency_ms、finish_reason。
9. 没有 usage 记录的模块：evaluation、memory、rag、benchmarks、vision；
   且所有记录的 token 数都是 `TokenEstimator` 估算，不是运行时 usage。
10. 未来需要接入在线 Provider 的模块：writing、evaluation（cloud judge）、
    memory（在线摘要）、adapter_evaluation（cloud 对比可选）。

## 3. Writing 调用链

### 3.1 Flutter 请求入口

- 页面：`apps/flutter_studio/lib/features/writing/writing_workspace_page.dart`
  （模型选择 `WritingModelSelector`、Adapter 下拉、生成参数面板）。
- 控制器：`apps/flutter_studio/lib/features/writing/writing_controller.dart`
  - `generate({...})` 默认 `stream = true`（约 183 行）；
  - `stream=false` 时走 `_api.generateWriting(request)`（约 222 行），否则走
    `_api.streamWriting(request)`（约 238 行）。
- API client：`apps/flutter_studio/lib/features/writing/writing_api_client.dart`
  - `POST /v1/writing/generate`
  - `POST /v1/writing/stream`（SSE，`writing_stream_event_dto.dart` 解析事件）
- 请求体 DTO：`apps/flutter_studio/lib/features/writing/models/writing_generation_request_dto.dart`
  - 默认值：temperature=0.8、topP=0.9、maxTokens=2048、repetitionPenalty=1.1、
    stream=true、stop=[]。
  - 页面输入框默认值同：`writing_workspace_page.dart`（约 50 行，`_temperature=0.8`
    `_topP=0.9` `_maxTokens=2048`）。

### 3.2 API Router

`llm_studio/api/routers/writing.py`：

- `POST /v1/writing/generate`：`WritingGenerationRequest` → `service.generate(body)`。
- `POST /v1/writing/stream`：SSE `StreamingResponse`，事件 start/delta/done/error/end；
  断连时调用 `service.cancel_generation`。
- `GET /v1/writing/generations`、`GET .../generations/{id}`、
  `POST .../save-to-chapter`、`POST .../cancel`。

请求结构（`llm_studio/writing/schemas.py`）：

```text
project_id, chapter_id, scene_id, template_id, template_version_id, context_id,
model_id(必填), adapter_id(可选), mode, target_length, user_variables, memory,
generation_params{temperature, top_p, max_tokens, repetition_penalty, stream, stop},
save_to_chapter
```

### 3.3 WritingService

`llm_studio/writing/service.py`：

- `generate()`（约 88 行）：`_prepare` → 创建 record（status=running）→
  `runtime_bridge.generate_text` → `split_at_stop` → `apply_length_control` →
  `_complete_record` → 可选 `save_output_to_chapter`。
- `stream_generate()`（约 191 行）：创建 record（status=streaming）→ 逐个 delta →
  每 0.5s 写回部分输出 → 结束时 `_complete_record`（latency=None）→ done/error 事件。
- `_prepare()`（约 305 行）：校验 mode（`GENERATION_MODES`，
  `llm_studio/writing/generation_modes.py`）、`normalize_target_length`、
  `_generation_params`（校验边界：temperature 0~2、top_p 0~1、max_tokens 1~32768、
  repetition_penalty 0.8~2）、校验 project/chapter/scene、对 user_variables
  做脱敏（`_safe_data`）。
- `_prepare_prompt()`（约 381 行）：
  - 若传 `context_id`：读取已保存的 context record，用
    `prompt_service.get_template/get_version` + `prompt_service.renderer.render`
    渲染（`llm_studio/prompts/renderer.py`）；
  - 否则调用 `context_service.assemble_and_render`（ContextAssembler +
    PromptRenderer + Memory retrieval 注入，见下）。
- `_create_record()`（约 500 行）：保存 model_id、adapter_id、generation_params、
  rendered prompt、input_context、input_token_estimate、prompt_hash、context_hash。
- `_complete_record()`（约 542 行）：保存 output、finish_reason、
  output_token_estimate（估算）、output_char_count、latency_ms。
- `_fail_record()`（约 558 行）：status=failed、finish_reason=error、error_code/message。

### 3.4 ContextAssembler / PromptRenderer

- 装配：`llm_studio/context/service.py`、`llm_studio/context/assembler.py`
  （选择/排序资料、预算控制、注入 Memory 检索结果）。
- 渲染：`llm_studio/prompts/renderer.py` `PromptRenderer.render`：
  system_prompt + role_prompt + instruction_template + output_constraints +
  negative_prompt 拼接，`{{variable}}` 替换；返回 missing_variables、warnings、
  prompt_hash。**渲染本身不调用模型**。

### 3.5 RuntimeBridge / Runtime

- `WritingRuntimeBridge._runner()`（`llm_studio/writing/runtime_bridge.py`）：
  - `resolve_runner(model_id, owner)` = `_get_or_load_runner`
    （`llm_studio/api_server.py` 约 568 行）：`_select_repository_model`
    → `select_model_for_chat`（`llm_studio/models/selection.py`）→ 按 id 或 auto
    选 READY 模型 → 未加载则 `create_runner` + 加锁加载。
  - 传 adapter_id 时：`adapter_repository.get(adapter_id)` + 加载/激活
    （`runner.list_loaded_adapters/load_adapter/activate_adapter`）。
- `generate_text()`：`runner.generate(prompt, **params)`（异步线程包装），
  返回 `RuntimeTextResult(text, finish_reason="stop", latency_ms)`。
- `stream_text()`：`runner.generate_stream(prompt, cancellation_token, **params)`；
  `_cancellations` 维护 CancellationToken 支持取消。
- `_runner_params()` 只透传 5 个参数：
  `temperature / top_p / max_tokens / repetition_penalty / stop`。
- Runner 侧（`llm_studio/runner.py` `_generation_config_from_kwargs`）：
  `max_tokens` 会被裁剪到配置上限 `generation.max_new_tokens`（默认 512，
  `config.yaml`），`stop` 列表透传给后端。

### 3.6 generation_records 保存逻辑

- 表：`llm_studio/writing/migrations.py`（generation_records）。
- 写入：`llm_studio/writing/repository.py`（create/update/list/get）。
- 记录字段（与 Gateway 相关的部分）：model_id、adapter_id、
  generation_params_json、input_token_estimate、output_token_estimate（均为估算）、
  output_char_count、latency_ms、finish_reason、error_code、error_message、
  prompt_hash、context_hash、status。
- 未发现真实 usage（prompt_tokens/completion_tokens）字段。

### 3.7 Streaming 支持情况

- 后端：`/v1/writing/stream`（SSE）；`WritingRuntimeBridge.stream_text`；
  `TransformersRunner.generate_stream`（TextIteratorStreamer + GenerationWorker，
  `llm_studio/generation/worker.py`）、`GGUFRunner.generate_stream`。
- 取消：`/v1/writing/generations/{id}/cancel` → `WritingService.cancel_generation`
  → `bridge.cancel_generation` → `CancellationToken`。
- 流式记录的 latency_ms 为 None（`_complete_record` 传 None）。
- Flutter：无流式开关 UI；`generate()` 默认 stream=true
  （`writing_workspace_page.dart` 的“生成”按钮未暴露 stream 参数）。

### 3.8 当前问题和风险

1. 模型调用被硬编码为“本地单模型”路径：`model_id` 是本地仓库 id，
   `_get_or_load_runner` 只认 LocalModelRepository（`llm_studio/models/selection.py`）。
2. 无 usage：token 数均为估算（`TokenEstimator`），不是运行时真实计数。
3. `finish_reason` 语义混合：bridge 固定 `"stop"`，长度控制再改
   `"length"`/`"stop"`/`"cancelled"`/`"unknown"`/`"error"`。
4. 错误映射在 bridge 内硬编码（MODEL_NOT_FOUND → WRITING_MODEL_NOT_FOUND 等），
   无统一 provider 错误层。
5. Streaming 没有 latency / usage 记录；断连取消依赖 SSE 连接生命周期。
6. `_current_model_id` 是全局单值，多请求并发选择不同模型时仅“最后一次”生效；
   实际 runner 按 model_path 缓存，模型切换依赖重复加载/卸载。
7. 每类业务（judge/摘要/对比）各自硬编码 generation_params
   （如 local_model_judge 固定 max_tokens=768），未来 provider 化时无统一入口。

## 4. Runtime / Models / Adapters 现状

### 4.1 模型注册

- `LocalModelRepository`（`llm_studio/models/repository.py`）：
  - 扫描：`ModelScanner`（`llm_studio/models/scanner.py`）扫描
    `models.root_dir` + 外部注册路径；
  - 元数据缓存：`data/model_index.json`（`layout.metadata_cache`，
    `llm_studio/models/storage.py`）。
- 实体：`llm_studio/models/entities.py` `LocalModel`：
  id、display_name、path、format（transformers/gguf/gptq/awq）、status、
  architecture、parameter_count、quantization、context_length、size_bytes、
  files、source_repo、revision。
- **未发现 provider 概念**：模型只有本地路径 + source_repo（下载来源），
  没有“模型来源提供方”（本地/在线）字段。

### 4.2 模型加载

- `_get_or_load_runner`（`llm_studio/api_server.py` 约 568 行）：
  `select_model_for_chat` → `create_runner` → `concurrency.model_load()` 锁 +
  `gpu_scheduler.acquire(MODEL_LOAD)` → `runner.load()`。
- 支持多模型注册（列表），但运行时 `_current_model_id` 是单值；
  `_runners` 可缓存多个已加载 runner（按 path）。

### 4.3 Adapter

- `AdapterManager`（`llm_studio/adapters/manager.py`）：PEFT
  `load_adapter/set_adapter/disable_adapter/delete_adapter`。
- 适配器仓库：`llm_studio/adapters/repository.py`；实体
  `llm_studio/adapters/entities.py` `AdapterInfo`：
  id、name、path、base_model_name_or_path、peft_type、rank、alpha、compatible。
- Adapter 绑定已加载 runner；一次仅激活一个 adapter。

### 4.4 Runtime 能力结论

| 能力 | 现状 | 证据 |
| --- | --- | --- |
| 多模型 | 列表支持，运行时单当前模型 | `api_server.py` `_runners` / `_current_model_id` |
| Adapter | 支持（PEFT） | `llm_studio/adapters/manager.py` |
| streaming | 支持 | `runner.py` `generate_stream` |
| usage | 无真实 usage | `GenerationResult` 仅有 text，token 字段恒 0（`llm_studio/generation/config.py`） |
| finish_reason | Runner 不返回 | bridge 固定 "stop" |
| 统一错误码 | 无 RUNTIME_ 前缀 | 见第 9 节 |
| 暴露上下文长度 | 元数据有 context_length，但生成配置用 config 的 max_context_tokens | `llm_studio/models/entities.py`、`llm_studio/runner.py` `_generation_config_from_kwargs` |
| 适合被 LocalRuntimeProvider 包装 | 是（接口集中、可适配） | `BaseRunner.generate/generate_stream` |

## 5. Evaluation 调用链

- 是否调用本地模型做 local_model_judge：是。
  `LocalModelJudgeEvaluator`（`llm_studio/evaluation/evaluators/local_model_judge.py`）
  经 `runtime_bridge.generate_text`，固定参数
  `{temperature: 0.2, top_p: 0.9, max_tokens: 768, repetition_penalty: 1.05, stop: []}`，
  `model_id` 来自 `evaluator_config.local_model_id`，`adapter_id=None`。
- 失败处理：捕获 `WritingRuntimeError`，降级为 warning finding，不影响整体评估
  （`_warning()`）。
- 装配：`llm_studio/evaluation/service.py` `_evaluator()`（约 431 行）：
  `use_local_model_judge` 开关 + `local_model_id` 校验；未配置/不可用时使用
  `LocalModelJudgeUnavailableEvaluator`。
- 是否已有 fake runtime 测试：是。`tests/test_evaluation_local_model_judge.py`
  使用 fake bridge；`tests/evaluation_stage11_utils.py` 提供工具。
- 未来 cloud_judge 接入点：`_evaluator()` 中新增 evaluator_type 分支或扩展现有
  judge evaluator；prompt 构造在 `local_model_judge.py::_prompt`。

## 6. Memory 摘要调用链

- 是否调用模型做章节摘要：是。
  `MemoryService.generate_chapter_summary`（`llm_studio/memory/service.py` 约 345 行）
  经 `self.writing_service.runtime_bridge.generate_text`，固定参数
  `{temperature: 0.3, top_p: 0.9, max_tokens: clamp(64, min(2048, max_chars*2)), repetition_penalty: 1.05, stop: []}`，
  `model_id` 由请求传入，`adapter_id=None`。
- 是否通过 WritingRuntimeBridge：是（复用 writing_service 的 bridge）。
- Prompt：`build_summary_prompt`（`llm_studio/memory/summaries.py`）。
- 记录：摘要表存 `generated_by="model"`、`model_id`、`prompt_template_id`。
- 是否需要在线模型摘要能力：未来需要（作为 cloud 摘要 Provider），接入点即
  `generate_chapter_summary` 中的 bridge 调用。

## 7. Adapter Evaluation 调用链

- base vs adapter 对比如何生成：
  `AdapterComparisonRunner.run_pair`（`llm_studio/adapter_evaluation/comparison_runner.py`）
  对同一冻结 prompt 依次调用：
  1. `runtime_bridge.generate_text(model_id=session.base_model_id, adapter_id=None)`；
  2. `runtime_bridge.generate_text(model_id=session.base_model_id, adapter_id=session.adapter_id)`。
- 是否直接调用 Runtime：通过 WritingRuntimeBridge（不直接接触 runner）。
- 结果：`AdapterVariantResult{status, finish_reason, output_hash, output_char_count,
  output_token_estimate, latency_ms, error_code, error_message}`
  （`llm_studio/adapter_evaluation/entities.py`）。
- 是否可以迁移到 ModelGateway：可以。把 `runtime_bridge.generate_text` 替换为
  gateway.generate（同一请求语义），adapter 组合由 ModelProfile 描述。
- fake runtime 测试：是（`tests/test_adapter_eval_service.py`、
  `tests/adapter_eval_stage9_utils.py`）。

## 8. Flutter 模型选择和生成参数现状

- Writing 页面模型选择：`writing_model_selector.dart`，列表来自
  `/v1/models`（本地模型）；无 provider / 来源标记。
- Writing 页面 Adapter 选择：`writing_workspace_page.dart`（约 300 行），
  列表来自 `/v1/adapters`；含“不使用 Adapter”空项。
- 生成参数默认值（页面 + DTO）：temperature=0.8、topP=0.9、
  maxTokens=2048、repetitionPenalty=1.1（`writing_workspace_page.dart` 约 50 行、
  `writing_generation_request_dto.dart`）。
- 是否支持 streaming 开关：未发现 UI 开关；controller `generate` 默认 stream=true，
  DTO 默认 stream=true。
- 是否有 Settings 默认模型：未发现独立“默认模型”设置项；
  `AppSettingsStore`（`apps/flutter_studio/lib/core/config/app_settings_store.dart`）
  保存 apiBaseUrl / apiKey / selectedModelId（selectedModelId 来自模型页选择）。
- 是否有模型来源 provider 概念：未发现（下载模块有 provider，但那是下载源）。
- 未来需要新增的 UI 控件：Provider/模型 Profile 选择器、流式开关、
  本地/在线切换、用量显示（tokens/latency）、provider 错误提示等。

## 9. 错误码和异常处理现状

- 统一错误码定义：`llm_studio/api/errors.py`（常量 + `api_error` /
  `error_payload`，HTTPException detail.error.code/message/request_id）。
- Writing 错误码：`WRITING_*`（`llm_studio/api/errors.py` 约 125 行起；
  `llm_studio/writing/errors.py` 映射 HTTP 状态）。
- Runtime 错误码：未发现 `RUNTIME_` 前缀；generation 层有
  `GENERATION_TIMEOUT / GENERATION_CANCELLED / CUDA_OUT_OF_MEMORY`
  （`llm_studio/api/errors.py`、`llm_studio/generation/exceptions.py`），
  bridge 将运行时异常统一映射为 `WRITING_GENERATION_FAILED` /
  `WRITING_STREAM_FAILED` / `WRITING_MODEL_NOT_FOUND` /
  `WRITING_MODEL_NOT_LOADED` / `WRITING_ADAPTER_NOT_FOUND`。
- Model 错误码：`MODEL_*`（MODEL_NOT_FOUND、MODEL_LOAD_BUSY、MODEL_LOAD_FAILED、
  MODEL_UNLOAD_FAILED、MODEL_DELETE_*、MODEL_NOT_LOADED、MODEL_LOADING）。
- Adapter 错误码：`ADAPTER_*`（ADAPTER_MODEL_REQUIRED、ADAPTER_NOT_FOUND、
  ADAPTER_INCOMPATIBLE、PEFT_NOT_AVAILABLE、ADAPTER_OPERATION_FAILED）。
- Evaluation / Memory / Adapter Eval 错误码：`EVALUATION_*`、`MEMORY_*`、
  `ADAPTER_EVAL_*`（`llm_studio/api/errors.py` 约 233 行起）。
- 长度相关：`WRITING_OUTPUT_BELOW_TARGET` 不是 HTTP 错误，而是 warnings 数组中的
  警告 code（`llm_studio/writing/length_control.py` 约 89 行），随
  `/v1/writing/generate` 响应与 `/v1/writing/stream` done 事件返回。
- Flutter 如何显示 error.code：`apps/flutter_studio/lib/core/errors/error_mapper.dart`
  `mapApiErrorMessage(code, fallback)` 将已知 code 映射为中文，未知 code
  `_ => fallback`（使用后端 message）；`api_exception.dart` 保留 code。
- 未来 Provider 错误码接入建议（本阶段不实现）：
  `MODEL_PROVIDER_UNAVAILABLE / MODEL_PROVIDER_AUTH_FAILED /
  MODEL_PROVIDER_RATE_LIMITED / MODEL_PROVIDER_TIMEOUT /
  MODEL_PROVIDER_BAD_RESPONSE / MODEL_PROVIDER_STREAM_FAILED /
  MODEL_PROVIDER_PRIVACY_CONFIRM_REQUIRED / MODEL_PROFILE_NOT_FOUND /
  MODEL_PROFILE_DISABLED`。

## 10. 配置、密钥和诊断脱敏现状

- 配置加载：`llm_studio/config.py`（YAML），路径可用环境变量
  `LLM_STUDIO_CONFIG` 覆盖（`config.py` 约 243 行）；`config.yaml` 位于项目根。
- 本地 API Key（客户端认证）：`llm_studio/admin.py` + `llm_studio/security.py`
  （argon2 hash）；用户文件 `./data/auth/api_users.json`
  （`config.yaml` auth.users_file），只存 hash 与 masked，不存明文；
  首次安装经 `/v1/setup/status` + `/v1/setup/initialize` 生成。
- Flutter 侧 API Key：`AppSettingsStore` 用 shared_preferences 明文保存
  `apiKey`（`apps/flutter_studio/lib/core/config/app_settings_store.dart` 约 55/81 行）。
- 环境变量读取机制：只有 `LLM_STUDIO_CONFIG`（配置路径）与
  `MODELSCOPE_API_TOKEN`（下载用，redaction 引用）；未发现 dotenv。
- secret manager：未发现。
- 敏感信息脱敏：
  - `llm_studio/security/redaction.py`：token/api_key/authorization/bearer。
  - `llm_studio/diagnostics/redaction.py`：`sk-`、bearer、x-api-key、authorization、
    本地路径；`config_io.redact_config` 脱敏配置导出。
  - writing / memory 服务保存记录前做 `_safe_data` / `_safe_text` 脱敏
    （`llm_studio/writing/service.py`、`llm_studio/memory/service.py`）。
- 诊断包是否脱敏：是（`llm_studio/diagnostics/collector.py` 对所有 payload 做
  redact_mapping/redact_path/redact_text，导出 config-redacted.json）。
- 未来在线 Provider API Key 的建议（本阶段不实现）：沿用 Flutter 本地保存 +
  请求时注入，不落库、不入日志、诊断包继续脱敏；如支持多 provider，应新增
  独立密钥存储引用。

## 11. 当前架构痛点

1. 模型入口分散：writing/eval/memory/adapter_eval/chat/rag/benchmarks 各自直接
   或经 bridge 调用 runner，无统一 generate 抽象。
2. 无 usage：tokens 全部为估算，latency 仅 writing 非流式与 adapter_eval 记录。
3. 无 provider 概念：model_id 绑定本地仓库，无法表达“在线模型”。
4. 错误码分散且桥接内硬编码映射，provider 化后无法表达认证/限流/超时。
5. Adapter 与“当前加载模型”强耦合（PEFT set_adapter），在线模型无此概念。
6. 并发模型状态为全局单值（`_current_model_id`），与多请求/多 profile 冲突。
7. 每类业务硬编码 generation_params，缺乏统一请求模型。

## 12. Model Gateway 改造影响范围

受影响（需要迁移调用点）：

- `llm_studio/writing/service.py`（generate / stream_generate）
- `llm_studio/evaluation/evaluators/local_model_judge.py`
- `llm_studio/memory/service.py`（generate_chapter_summary）
- `llm_studio/adapter_evaluation/comparison_runner.py`
- `llm_studio/api_server.py`（装配、`_get_or_load_runner` 包装为 LocalProvider）

受影响的数据/接口：

- generation_records（可能新增 provider/usage 字段——本阶段不改）
- `/v1/writing/*` 请求/响应（model_id 语义扩展——本阶段不改）
- Flutter writing / evaluation / memory / adapter_evaluation 页面
  （模型选择与 provider 切换——本阶段不改）

## 13. 不建议改动的稳定模块

- `llm_studio/runner.py`（BaseRunner 保持现状，由 LocalProvider 适配）
- `llm_studio/prompts/renderer.py`、`llm_studio/context/*`
  （Prompt 渲染与上下文装配与模型无关）
- `llm_studio/writing/length_control.py`、`generation_modes.py`
- `llm_studio/adapters/manager.py`（本地 PEFT 逻辑内聚）
- `llm_studio/models/*`（本地模型仓库保持本地语义）
- Novel 领域数据模型与数据库表

## 14. 审计结论

1. 当前所有 Novel Studio 模型调用已集中在单个 `WritingRuntimeBridge` 上，
   Gateway 化有清晰的替换点（bridge 接口 = 准 GenerateRequest/Result）。
2. 现状是纯本地单模型：无 provider、无真实 usage、无统一 finish_reason 语义。
3. 推荐改造顺序：先建 `llm_studio/model_gateway/` 核心（schemas / provider_base /
   service / local_provider / fake_provider / errors），再逐个迁移调用点
   （writing → adapter_evaluation → memory → evaluation），全程保持旧接口兼容。
4. 本阶段未修改任何业务代码；后续分阶段计划见
   `docs/MODEL_GATEWAY_MIGRATION_PLAN.md`，Phase 2 任务草案见
   `docs/MODEL_GATEWAY_PHASE2_CODEX_PROMPT.md`。
