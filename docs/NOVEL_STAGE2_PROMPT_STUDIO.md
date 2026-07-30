# Novel Studio Stage 2: Prompt Studio

阶段 2 在 Stage 1 小说基础资料库之上新增 Prompt Studio。它只负责模板、版本、变量校验和渲染预览，不调用 Runtime / Runner，不生成小说正文。

## 范围

- 新增 `llm_studio/prompts` 后端模块。
- 新增 `prompt_templates`、`prompt_template_versions`、`prompt_render_records`。
- 新增 `/v1/prompts/*` API。
- 新增 Flutter Prompt Studio 页面。
- 默认 Prompt 模板保存在 SQLite，不写死在 Flutter。

## 数据库表

- `prompt_templates`：模板元数据、类型、作用域、激活版本和软删除状态。
- `prompt_template_versions`：不可变模板版本，正文变更会创建新版本。
- `prompt_render_records`：预览渲染结果、缺失变量、warnings 和 `prompt_hash`。

## PromptRenderer

渲染顺序：

1. `system_prompt`
2. `role_prompt`
3. `instruction_template`
4. `output_constraints`
5. `negative_prompt`

规则：

- 只支持 `{{variable}}` 简单占位符。
- 合并顺序为 `default_values`、项目上下文、请求变量。
- `required=true` 且缺失时写入 `missing_variables`。
- 未声明变量会写入 `warnings`。
- 输出 `sha256` `prompt_hash`。
- 最大渲染长度为 200000 字符，超过返回 `PROMPT_RENDER_TOO_LONG`。
- 不读取本地文件，不执行代码，不访问网络。

## 变量语法

支持 `string`、`number`、`boolean`、`list`、`object`。

不支持 `if/else`、循环、函数调用、远程变量或文件读取。

## 默认模板

默认全局模板包括章节生成、章节续写、章节重写、润色、扩写、对白增强、场景扩写、大纲生成、人物生成和世界观生成。

通过 `POST /v1/prompts/defaults/ensure` 幂等初始化。已有模板不会被覆盖。

## API 示例

创建模板：

```json
{
  "name": "章节生成模板",
  "type": "chapter_generate",
  "scope": "global",
  "instruction_template": "小说标题：{{project_title}}\n章节大纲：{{chapter_outline}}\n请输出正文。",
  "variables_schema": {
    "project_title": {"type": "string", "required": true},
    "chapter_outline": {"type": "string", "required": true}
  },
  "default_values": {
    "target_length": "1200-1800 中文字符"
  }
}
```

渲染预览：

```json
{
  "template_id": "template-id",
  "project_id": "project-id",
  "chapter_id": "chapter-id",
  "variables": {
    "current_chapter_goal": "主角第一次进入黑市。",
    "pov": "第三人称"
  },
  "save_record": true
}
```

## Flutter 页面

Prompt Studio 页面支持模板列表、默认模板初始化、创建模板、JSON 变量 schema 编辑、JSON 默认值编辑、版本列表和渲染预览。

页面不会提供“生成正文”“发送到模型”“保存为 Dataset”等入口。

## 不包含内容

- Context Assembler
- WritingService
- Revision
- Dataset
- FineTune
- RAG / Memory
- Runtime / Runner 调用

## 阶段 3 前置条件

- 定义 Context Assembler 的输入结构。
- 定义上下文预算、截断和排序策略。
- 明确 Prompt 渲染结果如何进入 Writing 阶段。
