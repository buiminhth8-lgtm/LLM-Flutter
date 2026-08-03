# Novel Studio Roadmap

Novel Studio is developed in stages on top of the existing LLM-Studio backend
and Flutter Windows client.

Stage 2 Prompt Studio details: [NOVEL_STAGE2_PROMPT_STUDIO.md](NOVEL_STAGE2_PROMPT_STUDIO.md).
Stage 3 Context Assembler details: [NOVEL_STAGE3_CONTEXT_ASSEMBLER.md](NOVEL_STAGE3_CONTEXT_ASSEMBLER.md).
Stage 4 Writing details: [NOVEL_STAGE4_WRITING.md](NOVEL_STAGE4_WRITING.md).
Stage 5 Revisions details: [NOVEL_STAGE5_REVISIONS.md](NOVEL_STAGE5_REVISIONS.md).
Stage 6 Dataset Builder details: [NOVEL_STAGE6_DATASET_BUILDER.md](NOVEL_STAGE6_DATASET_BUILDER.md).
Stage 7 Dataset Versioning details: [NOVEL_STAGE7_DATASET_VERSIONING.md](NOVEL_STAGE7_DATASET_VERSIONING.md).
Stage 8 Fine-tune Center details: [NOVEL_STAGE8_FINETUNE_CENTER.md](NOVEL_STAGE8_FINETUNE_CENTER.md).
Stage 9 Adapter Evaluation details: [NOVEL_STAGE9_ADAPTER_EVALUATION.md](NOVEL_STAGE9_ADAPTER_EVALUATION.md).
Stage 10 RAG / Memory details: [NOVEL_STAGE10_RAG_MEMORY.md](NOVEL_STAGE10_RAG_MEMORY.md).

Current implemented scope reaches Stage 10: completed Stage 8 Adapters can be
compared in Stage 9, and Stage 10 can build long-form novel Memory from existing
novel data, retrieve relevant chunks, persist retrieval traces, maintain chapter
summary versions, and inject budgeted memory into ContextAssembler.

Stage 10 boundaries:

- `revision_records` saves `original_text`, `edited_text`, `diff_json`, tags, score, status, hashes, and `accepted_for_dataset`.
- `revision_autosaves` saves editing drafts separately and never changes formal revision text.
- `training_datasets`, `training_samples`, and `dataset_exports` are mutable draft builder records.
- `dataset_versions` and `training_recipes` are frozen/configuration inputs for Stage 8 training.
- `finetune_runs` records LoRA/QLoRA training lifecycle and registered adapters.
- `adapter_evaluation_*` records compare base vs adapter outputs and manual evaluation data.
- `memory_*` records persist novel memory documents, chunks, index entries, and retrieval traces.
- `chapter_summary_versions` stores manual or model-generated summary versions.
- Full automatic Evaluation Center, automatic literary scoring, DPO/RLHF, and external vector database dependency remain later stages / out of scope.

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

- `confirmed` training recipe + `frozen` DatasetVersion 可创建 `finetune_runs`。
- 训练任务通过 JobQueue 后台执行，并受 GPU Scheduler 保护。
- 记录 metrics、logs、last checkpoint、best checkpoint、取消与 resume 状态。
- 训练完成后注册 Adapter，但默认不自动激活。
- 不包含 Adapter 评估、基础模型 vs Adapter 对比、RAG/Memory 或 Evaluation Center。

## 阶段 9：Adapter 评估与生成对比

- 已完成 Stage 8 Adapter 与基础模型的同 Prompt / 同上下文生成对比。
- `adapter_evaluation_*` 表持久化 session、case、result、manual score 和 report。
- 评估用例复用 ContextAssembler、PromptRenderer 与 WritingRuntimeBridge。
- 支持人工 winner / 1～5 score / dimension notes，以及轻量报告。
- 支持显式从评估结果创建 Stage 5 Revision，但不创建训练样本。
- 不包含自动风格/人物/剧情评分、RAG/Memory、DPO/RLHF、训练或 Adapter 自动激活。

## 阶段 10：长篇小说 RAG / Memory 增强

- `memory_documents` 保存章节摘要/正文、人物卡、世界观、剧情线、时间线、修订稿和手动记忆。
- `memory_chunks` 按中文友好的段落/字符规则切块。
- `memory_index_entries` 默认 keyword，SQLite FTS5 可用时额外建立 FTS，失败时回退 keyword。
- `memory_retrieval_records` 保存 query、top_k、预算、召回/选中 chunks 和 warnings。
- `chapter_summary_versions` 支持手动摘要和复用 WritingRuntimeBridge 的模型摘要。
- ContextAssembler 在 `memory.enabled=true` 时注入 `retrieved_memory`，关闭时保持 Stage 3 原行为。
- Flutter 新增 Memory Center、检索预览、章节摘要控件，并在 Writing Workspace 加 Memory 开关。
- 不包含完整 Evaluation Center、自动文学评分、训练、DPO/RLHF 或外部向量库强依赖。

## 阶段 11：Evaluation Center 完整评估中心

## 阶段 12：UI 产品化与 Windows 发布验收
