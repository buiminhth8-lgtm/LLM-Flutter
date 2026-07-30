# Novel Studio 阶段 3：Context Assembler

阶段 3 在 Novel 基础资料库和 Prompt Studio 之上增加上下文装配能力。它负责选择、排序、格式化和裁剪小说资料，输出与 Stage 2 `PromptRenderer` 兼容的变量包。该阶段不调用 Runtime / Runner，不生成小说正文。

## 范围

- 新增 `llm_studio/context` 后端模块。
- 新增 `context_assembly_records` SQLite 表。
- 新增 `/v1/context/*` API。
- 新增 Flutter `Context Preview` 页面。
- 支持字符预算、近似 Token 预算、优先级裁剪、记录追溯和 Prompt 渲染预览。

## 标准变量

装配结果可包含：

- 项目：`project_title`、`genre`、`description`、`target_style`、`target_audience`
- 章节：`chapter_title`、`chapter_outline`、`chapter_summary`、`previous_chapter_summary`
- 场景：`scene_title`、`scene_outline`、`scene_location`、`scene_pov_character`
- 资料：`characters`、`main_characters`、`world_setting`、`plot_threads`、`timeline`
- 用户输入：`current_chapter_goal`、`target_length`、`style`、`pov`、`user_instruction`、`forbidden_content`

变量优先级为：用户显式输入 > 场景/章节 > 项目资料 > Prompt 默认值。缺失资料返回空字符串或 warning，不返回 `null`。

## Token 与字符预算

阶段 3 不加载 tokenizer。`TokenEstimator` 使用稳定的本地近似规则：

- 中文字符按 1.1 token 估算。
- 英文单词按 1.3 token 估算。
- 标点、空白和换行按 0.25 token 估算。

预算字段包括 `max_tokens`、`reserved_output_tokens`、`max_context_tokens`、`max_chars` 和 `hard_limit`。实际资料预算取 `max_context_tokens` 与 `max_tokens - reserved_output_tokens` 的较小值。估算接口不访问网络或模型。

## Selector 优先级

- 人物：POV 人物、关联人物、主角/主要人物、其他人物；默认最多 8 个。
- 世界观：场景地点匹配、高 `priority`、核心类别；默认最多 12 条。
- 剧情线：`in_progress`、`open`、关联人物、高 `priority`；默认最多 5 条。
- 时间线：当前章节/场景相关事件和当前章节之前的最近事件；默认最多 10 条。
- 上一章：优先使用上一章 `summary`；没有摘要时可使用正文片段并返回 warning，不自动生成摘要。

## 截断策略

预算不足时按以下顺序裁剪：

1. 低优先级世界观条目。
2. 时间线事件。
3. 剧情线。
4. 上一章摘要。
5. 人物背景与备注等次要详情。
6. `hard_limit=true` 且仍严重超限时，最后裁剪自动装配的章节大纲。

用户显式输入和当前章节目标不会被裁剪。发生裁剪时返回 `CONTEXT_TRUNCATED` warning；核心资料仍超限时返回 `CONTEXT_BUDGET_EXCEEDED` warning。

## API

- `POST /v1/context/assemble`：装配变量，不渲染 Prompt。
- `POST /v1/context/render-preview`：装配变量并复用 Stage 2 `PromptRenderer`。
- `POST /v1/context/estimate`：估算文本或变量的 Token/字符数。
- `GET /v1/context/records`：查询装配记录。
- `GET /v1/context/records/{context_id}`：查询单条装配记录。

示例：

```json
{
  "project_id": "project-id",
  "chapter_id": "chapter-id",
  "template_id": "template-id",
  "mode": "chapter_generate",
  "target_budget": {
    "max_tokens": 4096,
    "reserved_output_tokens": 1200,
    "max_context_tokens": 2500,
    "max_chars": 12000,
    "hard_limit": true
  },
  "user_variables": {
    "current_chapter_goal": "主角第一次进入黑市。",
    "pov": "第三人称",
    "target_length": "1200-1800 中文字符"
  },
  "save_record": true
}
```

## Flutter 页面

当 `/v1/capabilities` 返回 `context_assembler=available` 且 `frontend_exposed=true` 时，Novel Studio 导航显示 `Context Preview`。页面支持项目、章节、场景和 Prompt 模板选择，预算输入，变量与选中资料预览，warning 展示，以及变量 JSON/渲染 Prompt 复制。

## 不包含内容

- WritingService 或 `/v1/writing`
- Runtime / Runner 调用
- Revision、Dataset、FineTune
- RAG、embedding 或 vector database
- 自动章节摘要生成

## 阶段 4 前置条件

- generation record 必须引用 `context_id`、`context_hash`、模板版本和模型配置。
- Stage 4 只能消费 Stage 3 装配结果，不能在 WritingService 中重复实现资料选择和预算逻辑。
- 需要定义生成取消、流式输出、GPU 调度和失败重试契约。
- 模型输出与上下文、Prompt 记录应分别保存，便于审计与后续 Revision。
