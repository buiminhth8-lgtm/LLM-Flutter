# Novel Studio Roadmap

Novel Studio is developed in stages on top of the existing LLM-Studio backend
and Flutter Windows client.

## 阶段 0：工程基线整理与开发入口

- 不开发业务功能。
- 新增 feature flag。
- 新增 capabilities 占位。
- 确认现有 LLM-Studio 基础能力稳定。

## 阶段 1：Novel 项目与基础资料库

- `novel_projects`
- `novel_volumes`
- `novel_chapters`
- `novel_scenes`
- `novel_characters`
- `novel_world_entries`
- `novel_plot_threads`
- `novel_timeline_events`

阶段 1 已新增基础 CRUD、SQLite repository、`/v1/novels/*` API 和 Flutter
基础页面。详情见 [NOVEL_STAGE1_FOUNDATION.md](NOVEL_STAGE1_FOUNDATION.md)。

## 阶段 2：Prompt Studio 模板系统

## 阶段 3：Context Assembler 上下文装配

## 阶段 4：Writing 本地小说生成闭环

## 阶段 5：Revision 人工修订与版本系统

## 阶段 6：Dataset Builder 数据集构建

## 阶段 7：Dataset Version 冻结与训练配方推荐

## 阶段 8：LoRA / QLoRA Fine-tune Center

## 阶段 9：Adapter 评估与生成对比

## 阶段 10：长篇小说 RAG / Memory 增强

## 阶段 11：Evaluation Center 完整评估中心

## 阶段 12：UI 产品化与 Windows 发布验收
