# Novel Studio 阶段 2：提示词工作室

本文档为阶段归档版，已删除重复验收长列表，保留范围、边界、数据资产和前后置关系。

## 范围

实现提示词模板、版本、变量校验和渲染预览。

## 默认模板

- 内置 24 个中文小说创作默认模板，按用途分为三类：
  - 正文生成类（12 个）：章节正文、续写、重写、润色、扩写、压缩、场景扩写、
    动作戏、情绪戏、悬念戏、对白增强、冲突升级；
  - 规划设定类（8 个）：总大纲、分卷大纲、章节大纲、人物小传、人物关系、
    世界观、势力组织、伏笔设计；
  - 辅助编辑类（4 个）：章节摘要、前情提要、一致性检查、人工修订建议。
- 每个默认模板都包含 `system_prompt` / `role_prompt` /
  `instruction_template` / `output_constraints` / `negative_prompt` /
  `variables_schema` / `default_values`，并通过 `metadata` 记录
  `builtin_key`、`language`、`category`、`recommended` 与 `version`。
- 安装与升级采用幂等策略，且不覆盖用户修改：
  1. 按 `metadata.builtin_key` 匹配模板；不存在则安装。
  2. 安装时在 `metadata.content_hash` 中记录内容哈希。
  3. 已安装模板的 active 内容哈希与 `content_hash` 不一致时，
     视为用户修改，跳过且不覆盖。
  4. 内容一致但落后于内置版本时，升级为新版本并刷新 `content_hash`。
  5. 没有 builtin 元数据的模板视为用户模板，永远不覆盖。
- `POST /v1/prompts/defaults/ensure` 返回
  `installed_count` / `skipped_count` / `upgraded_count` /
  `user_modified_count` / `template_keys` 汇总。

## 主要资产

- 后端领域模块按阶段分层复用。
- Flutter 页面只调用后端 API，不在前端实现核心业务事实。
- 数据库表与记录均保持阶段边界。

## 边界

不调用模型，不保存生成记录。

## 验收

- 后端测试通过。
- Flutter analyze/test 按环境执行。
- 能力清单状态与阶段目标一致。
- 不保存 API Key、Cookie、Authorization 或本机敏感绝对路径。

## 相关

返回 [Novel Studio 路线图](NOVEL_STUDIO_ROADMAP.md)。
