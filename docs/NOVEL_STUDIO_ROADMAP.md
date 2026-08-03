# Novel Studio 路线图

Novel Studio 是 LLM-Studio 的小说生产工作台。路线按阶段推进，每个阶段保持边界清晰，避免生成、修订、数据集、训练和评估互相隐式触发。

| 阶段 | 名称 | 状态 | 归档文档 |
| --- | --- | --- | --- |
| 0 | 基线预留 | 已归档 | [NOVEL_STAGE0_BASELINE.md](NOVEL_STAGE0_BASELINE.md) |
| 1 | 基础资料库 | 已归档 | [NOVEL_STAGE1_FOUNDATION.md](NOVEL_STAGE1_FOUNDATION.md) |
| 2 | 提示词工作室 | 已归档 | [NOVEL_STAGE2_PROMPT_STUDIO.md](NOVEL_STAGE2_PROMPT_STUDIO.md) |
| 3 | 上下文装配 | 已归档 | [NOVEL_STAGE3_CONTEXT_ASSEMBLER.md](NOVEL_STAGE3_CONTEXT_ASSEMBLER.md) |
| 4 | 写作生成闭环 | 已归档 | [NOVEL_STAGE4_WRITING.md](NOVEL_STAGE4_WRITING.md) |
| 5 | 人工修订 | 已归档 | [NOVEL_STAGE5_REVISIONS.md](NOVEL_STAGE5_REVISIONS.md) |
| 6 | 数据集构建 | 已归档 | [NOVEL_STAGE6_DATASET_BUILDER.md](NOVEL_STAGE6_DATASET_BUILDER.md) |
| 7 | 版本冻结与配方 | 已归档 | [NOVEL_STAGE7_DATASET_VERSIONING.md](NOVEL_STAGE7_DATASET_VERSIONING.md) |
| 8 | 微调中心 | 已归档 | [NOVEL_STAGE8_FINETUNE_CENTER.md](NOVEL_STAGE8_FINETUNE_CENTER.md) |
| 9 | 适配器评估 | 已归档 | [NOVEL_STAGE9_ADAPTER_EVALUATION.md](NOVEL_STAGE9_ADAPTER_EVALUATION.md) |
| 10 | 记忆 / RAG | 已归档 | [NOVEL_STAGE10_RAG_MEMORY.md](NOVEL_STAGE10_RAG_MEMORY.md) |
| 11 | 完整评估中心 | 已归档 | [NOVEL_STAGE11_EVALUATION_CENTER.md](NOVEL_STAGE11_EVALUATION_CENTER.md) |
| 12 | UI 产品化与 Windows 发布 | 已归档 | [NOVEL_STAGE12_PRODUCTIZATION.md](NOVEL_STAGE12_PRODUCTIZATION.md) |

## 总体边界

- 写作生成只产生 generation_records。
- 人工修订只产生 revision_records。
- 数据集构建必须由用户显式选择候选修订。
- DatasetVersion 冻结后不可原地修改。
- 训练必须从冻结版本和确认配方启动。
- 评估只读，不自动改写正文或训练数据。

## Flutter 入口

Novel 模块是否显示由 `features.novel_studio.enabled` 与 `/v1/capabilities` 共同决定。修改配置后需要重启后端并刷新 Flutter 能力。
