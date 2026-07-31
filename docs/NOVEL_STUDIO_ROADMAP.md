# Novel Studio Roadmap

Novel Studio is developed in stages on top of the existing LLM-Studio backend
and Flutter Windows client.

Stage 2 Prompt Studio details: [NOVEL_STAGE2_PROMPT_STUDIO.md](NOVEL_STAGE2_PROMPT_STUDIO.md).
Stage 3 Context Assembler details: [NOVEL_STAGE3_CONTEXT_ASSEMBLER.md](NOVEL_STAGE3_CONTEXT_ASSEMBLER.md).
Stage 4 Writing details: [NOVEL_STAGE4_WRITING.md](NOVEL_STAGE4_WRITING.md).
Stage 5 Revisions details: [NOVEL_STAGE5_REVISIONS.md](NOVEL_STAGE5_REVISIONS.md).
Stage 6 Dataset Builder details: [NOVEL_STAGE6_DATASET_BUILDER.md](NOVEL_STAGE6_DATASET_BUILDER.md).
Stage 7 Dataset Versioning details: [NOVEL_STAGE7_DATASET_VERSIONING.md](NOVEL_STAGE7_DATASET_VERSIONING.md).

Stage 6 is implemented: approved revision candidates can be converted into
reviewable SFT samples, sample review state is persisted, and approved samples
can be exported as draft JSONL files.

Stage 6 boundaries:

- `revision_records` saves `original_text`, `edited_text`, `diff_json`, tags, score, status, hashes, and `accepted_for_dataset`.
- `revision_autosaves` saves editing drafts separately and never changes formal revision text.
- `training_datasets`, `training_samples`, and `dataset_exports` are mutable draft builder records.
- FineTuneRun, LoRA / QLoRA execution, Adapter registration, RAG/Memory, and Evaluation remain later stages.

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

- `generation_records` 持久化 Prompt、上下文、模型参数、输出和状态。
- 支持非流式生成、SSE 流式生成、取消和保存到章节草稿/摘要。
- Flutter Writing Workspace 提供 Context Preview、生成参数、输出和历史。
- 不包含 Revision、Diff、Dataset 或自动训练。

## 阶段 5：Revision 人工修订与版本系统

## 阶段 6：Dataset Builder 数据集构建

- `accepted_for_dataset=true` 且经过用户选择的 revision 可转换为 SFT sample。
- `training_samples` 支持 pending / approved / rejected / archived 审核状态。
- 导出 draft SFT JSONL 到 `data/datasets/{dataset_id}`，不创建 DatasetVersion，不启动训练。

## 阶段 7：Dataset Version 冻结与训练配方推荐

- `ready` / `dirty` dataset 可冻结为不可变 `dataset_versions`。
- 写出 `train.jsonl`、可选 `val.jsonl` 和 `manifest.json`。
- 支持 exact dedupe、near duplicate warning、grouped train/val split、token 估算。
- 支持 draft `training_recipes` 推荐和 confirm，但不启动训练。

## 阶段 8：LoRA / QLoRA Fine-tune Center

## 阶段 9：Adapter 评估与生成对比

## 阶段 10：长篇小说 RAG / Memory 增强

## 阶段 11：Evaluation Center 完整评估中心

## 阶段 12：UI 产品化与 Windows 发布验收
