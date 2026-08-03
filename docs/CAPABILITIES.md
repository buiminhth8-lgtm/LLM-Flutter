# 能力清单

`GET /v1/capabilities` 是 Flutter 导航和功能开关的事实来源。

## 关键能力

| 能力 | 含义 |
| --- | --- |
| `novel_studio` | 小说工作台总入口 |
| `prompt_studio` | 提示词模板与渲染预览 |
| `context_assembler` | 小说上下文装配 |
| `writing_workspace` | 写作生成工作区 |
| `revision_system` | 人工修订系统 |
| `dataset_builder` | 数据集构建 |
| `dataset_versioning` | 数据集版本冻结 |
| `finetune_center` | LoRA / QLoRA 微调中心 |
| `adapter_evaluation` | 适配器对比评估 |
| `novel_rag_memory` | 长篇记忆 / RAG |
| `full_evaluation_center` | 完整评估中心 |

## 前端行为

- 能力可用时显示入口。
- 能力不可用时显示中文提示。
- `features.novel_studio.enabled=false` 时 Novel 相关入口不可用。
