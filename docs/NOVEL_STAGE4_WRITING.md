# Novel Studio 阶段 4：Writing 本地小说生成闭环

阶段 4 在 Novel 基础资料库、Prompt Studio 和 Context Assembler 之上增加本地小说生成能力。生成请求始终由后端装配上下文、渲染 Prompt，并通过现有 `LocalModelRepository`、Runner、并发控制和 GPU Scheduler 调用本地模型；Flutter 不加载模型，也不拼接完整 Prompt。

## 范围

- 新增 `llm_studio/writing` 后端模块和 `generation_records` SQLite 表。
- 新增 `/v1/writing/*` API，支持非流式生成、SSE 流式生成、取消、查询记录和保存到章节。
- 新增 Flutter `Writing Workspace`，支持项目、章节、场景、Prompt、模型、Adapter、长度和生成参数选择。
- 保存渲染 Prompt、上下文快照、模型与 Adapter ID、生成参数、输出、哈希、状态、耗时和近似 Token/字符统计。
- 只允许把成功输出保存到 `draft_content` 或 `summary`，不写 `final_content`。

## WritingService 流程

非流式流程：

1. 校验项目、章节、场景、写作模式、目标长度和生成参数。
2. 调用 Stage 3 `ContextService.assemble_and_render`；该方法内部复用 Stage 2 `PromptRenderer`。
3. 创建 `generation_records`，状态设为 `running`。
4. `WritingRuntimeBridge` 通过应用现有 runner resolver 获取或自动加载本地模型，并复用 inference concurrency 与 GPU Scheduler。
5. 调用 runner `generate`，应用停止词和中文长度控制。
6. 保存完整输出、SHA-256、统计和 `finish_reason`，状态设为 `succeeded`；异常则保存脱敏错误并设为 `failed`。

流式流程创建状态为 `streaming` 的记录，通过 SSE 发送 `start`、`delta`、`done` 或 `error`。后端持续累积输出并周期性落库；完成、取消和异常时都会保存当前完整或部分输出。取消使用现有 `CancellationToken`，不创建第二套 Runtime。

## GenerationRecord

`generation_records` 的主要字段：

| 字段 | 含义 |
| --- | --- |
| `id` | 生成记录 ID，API 中返回为 `generation_id` |
| `project_id` / `chapter_id` / `scene_id` | Novel 资料关联 |
| `template_id` / `template_version_id` | Prompt 模板及不可变版本 |
| `context_id` / `context_hash` | Context Assembler 记录与内容哈希 |
| `model_id` / `adapter_id` | 模型仓库 ID 与可选 Adapter ID |
| `mode` | 写作模式 |
| `prompt_rendered` / `prompt_hash` | 后端渲染的最终 Prompt 与哈希 |
| `input_context_json` | 脱敏后的变量、选中资料和 warning |
| `model_output` / `output_hash` | 模型原始生成输出与 SHA-256 |
| `generation_params_json` | 温度、Top P、最大 Token、重复惩罚、停止词 |
| `target_length_json` | 目标长度单位、最小值、最大值和策略 |
| `status` / `finish_reason` | 生命周期和结束原因 |
| 统计字段 | 输入/输出 Token 估算、输出字符数和耗时 |
| 错误字段 | 脱敏后的稳定错误码和消息 |

记录不保存 API Key、Authorization、Cookie、密码、模型绝对路径或其他敏感本机路径。

## 写作模式

- `chapter_generate`：根据章节大纲生成正文
- `chapter_continue`：基于当前草稿续写
- `chapter_rewrite`：重写章节或片段
- `chapter_polish`：语言润色
- `chapter_expand`：扩写章节
- `dialogue_enhance`：增强对白
- `scene_expand`：扩写场景
- `summary_generate`：生成摘要
- `custom`：自定义指令

未知模式返回 `WRITING_INVALID_MODE`。每个模式映射到同名 Prompt template type。

## 中文长度控制

默认单位为 `chars`，字符统计去除首尾空白并忽略正文中的空格和换行，中文、英文和标点均计入。`tokens` 使用 Stage 3 的稳定近似估算器。

- `soft`：超出最大值时保留完整输出并返回 warning。
- `hard`：超出最大值时截断并返回 `finish_reason=length`。
- 低于最小值时返回 warning，不自动补写。
- 未显式提供 `max_tokens` 时，根据目标长度建议输出预算；阶段 4 不执行多轮自动补写。

## API

- `POST /v1/writing/generate`
- `POST /v1/writing/stream`
- `GET /v1/writing/generations`
- `GET /v1/writing/generations/{generation_id}`
- `POST /v1/writing/generations/{generation_id}/save-to-chapter`
- `POST /v1/writing/generations/{generation_id}/cancel`

非流式请求示例：

```json
{
  "project_id": "project-id",
  "chapter_id": "chapter-id",
  "template_id": "template-id",
  "model_id": "qwen-local",
  "adapter_id": null,
  "mode": "chapter_continue",
  "target_length": {
    "unit": "chars",
    "min": 1200,
    "max": 1800,
    "strategy": "soft"
  },
  "user_variables": {
    "current_chapter_goal": "主角进入黑市，第一次发现灵骨交易。",
    "style": "紧张、压迫、细节丰富"
  },
  "generation_params": {
    "temperature": 0.8,
    "top_p": 0.9,
    "max_tokens": 2048,
    "repetition_penalty": 1.1,
    "stream": false,
    "stop": []
  }
}
```

SSE 事件：

```json
{"type":"start","generation_id":"generation-id"}
{"type":"delta","text":"夜色"}
{"type":"done","generation_id":"generation-id","finish_reason":"stop"}
{"type":"error","generation_id":"generation-id","error_code":"WRITING_STREAM_FAILED","message":"..."}
```

保存请求只接受：

```json
{"target":"draft_content","append":false}
```

也可将 `target` 设为 `summary`。`final_content` 会返回 `WRITING_SAVE_TARGET_NOT_ALLOWED`。

## Flutter Writing Workspace

当 `/v1/capabilities` 返回 `writing_workspace=available` 且 `frontend_exposed=true` 时，Creative 导航显示 `Writing`。

- 左侧：项目、章节、场景和当前章节草稿。
- 中间：流式 AI 输出、停止、Save to Draft、Append to Draft、warning 和生成历史。
- 右侧：写作模式、Prompt、模型、Adapter、章节目标、目标长度、生成参数和 Context Preview。
- 页面销毁时取消 SSE subscription；Stop 调用后端取消接口。
- Flutter 可以展示后端返回的 warning，但最终 Prompt、长度控制和生成记录均以后端为准。

## Feature flag、权限与 capabilities

`features.novel_studio.enabled=false` 时，`/v1/writing/*` 返回 `WRITING_FEATURE_DISABLED`。初版 RBAC 复用项目角色模型：viewer 可读取生成记录，operator/admin 可生成、取消和保存。

启用 Novel Studio 后：

- `writing_workspace=AVAILABLE`
- `writing_stream=AVAILABLE`
- `writing_save_to_chapter=AVAILABLE`
- `revision_system=NOT_IMPLEMENTED`
- `dataset_builder=NOT_IMPLEMENTED`
- `novel_rag_memory=NOT_IMPLEMENTED`
- `novel_evaluation=NOT_IMPLEMENTED`

## 不包含内容

- Revision 人工修订和 Diff
- Dataset Builder、训练样本和 JSONL 导出
- Novel 专用 LoRA / QLoRA 训练流程
- 自动评估
- 长篇小说 RAG / Memory
- 自动把生成结果加入训练数据
- 自动覆盖 `final_content`

## 阶段 5 前置条件

- Stage 5 只读取 `generation_records.model_output` 作为模型原文，不能改变 Stage 4 记录。
- Revision 必须拥有独立表、状态、人工编辑内容和 Diff。
- Save to Draft 与创建 Revision 必须保持两个明确动作。
- 任何 Dataset 候选标记都不能在阶段 5 自动创建训练样本。
