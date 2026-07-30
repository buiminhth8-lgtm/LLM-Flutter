# LLM-Studio Novel Studio 方案设计

## 0. 产品定位

在现有 `LLM-Studio` 基础上扩展一个小说创作工作台，暂定模块名：

```text id="pp68em"
Novel Studio
```

核心目标：

```text id="75yu52"
1. 加载本地大语言模型。
2. 使用本地模型进行小说创作。
3. 支持自定义 Prompt 控制输出内容、长度、风格、人物、剧情走向。
4. 支持人工修改模型输出。
5. 将人工修改结果沉淀为训练数据。
6. 后续使用 LoRA / QLoRA 对本地模型进行风格调优。
```

整体闭环：

```text id="ek5u7l"
本地模型加载
→ Prompt 模板编排
→ 小说生成
→ 人工编辑
→ Diff 对比
→ 保存修订记录
→ 构建 SFT / Preference 数据集
→ LoRA / QLoRA 微调
→ 加载 Adapter
→ 再次生成和评估
```

---

# 1. 复用现有 LLM-Studio 架构

## 1.1 可直接复用的已有能力

现有 LLM-Studio 已经具备这些基础模块：

```text id="qb0ldh"
1. 本地模型扫描、加载、卸载。
2. Runtime / Runner 推理接口。
3. Streaming Chat。
4. Adapter / LoRA 管理。
5. Job Queue 后台任务。
6. GPU Scheduler。
7. 下载模块。
8. Storage Cleanup。
9. Diagnostics。
10. Capabilities 能力表。
11. Flutter Windows 桌面客户端。
12. API Key / RBAC / error.code。
13. Python FastAPI 后端服务。
```

Novel Studio 不应该另起一套模型系统，而应该复用：

```text id="7zd2ei"
llm_studio/models/
llm_studio/runtime/
llm_studio/adapters/
llm_studio/jobs/
llm_studio/storage/
llm_studio/api/errors.py
apps/flutter_studio/lib/core/api/
apps/flutter_studio/lib/core/ui/
```

---

## 1.2 新增模块

新增后端模块：

```text id="0a9xti"
llm_studio/novels/        # 小说项目、章节、人物、世界观
llm_studio/prompts/       # Prompt 模板、变量、渲染
llm_studio/writing/       # 小说生成、续写、改写、润色
llm_studio/revisions/     # 人工修改、版本、diff
llm_studio/datasets/      # SFT / Preference 数据集构建与导出
llm_studio/finetune/      # LoRA / QLoRA 训练任务
llm_studio/evaluation/    # 风格、连贯性、人物一致性评估
```

新增 Flutter 页面：

```text id="0k82j4"
Novel Projects
Prompt Studio
Writing Workspace
Revision Review
Dataset Builder
Fine-tune Center
Evaluation Center
```

---

# 2. 总体架构

## 2.1 后端架构

```text id="8bgpn2"
FastAPI API Layer
    ↓
Novel Service
Prompt Service
Writing Service
Revision Service
Dataset Service
FineTune Service
Evaluation Service
    ↓
SQLite Repository Layer
    ↓
Runtime / ModelRepository / AdapterManager / JobQueue / GPU Scheduler
```

核心调用链：

```text id="h6f1xn"
Flutter Writing Workspace
    ↓
POST /v1/novels/{project_id}/chapters/{chapter_id}/generate
    ↓
WritingService
    ↓
PromptRenderer
    ↓
Runtime.generate / Runtime.stream
    ↓
返回模型输出
    ↓
用户人工编辑
    ↓
RevisionService 保存 original / edited / diff
    ↓
DatasetService 生成训练样本
```

---

## 2.2 前端架构

Flutter 继续采用当前工程化结构：

```text id="053wpf"
apps/flutter_studio/lib/
├── core/
│   ├── api/
│   ├── ui/
│   ├── errors/
│   └── models/
└── features/
    ├── novels/
    ├── prompt_studio/
    ├── writing/
    ├── revisions/
    ├── datasets/
    ├── finetune/
    └── evaluation/
```

每个 feature 保持：

```text id="85aus7"
controller
state
page
widgets
dto
```

例如：

```text id="xmp860"
features/writing/
├── writing_controller.dart
├── writing_state.dart
├── writing_page.dart
├── widgets/
│   ├── chapter_editor.dart
│   ├── generation_panel.dart
│   ├── prompt_preview_panel.dart
│   └── revision_diff_view.dart
```

---

# 3. 数据模型设计

## 3.1 小说项目表

```sql id="43tiy9"
novel_projects
- id
- title
- genre
- description
- target_style
- target_audience
- status
- created_at
- updated_at
```

用途：

```text id="co8xhx"
保存一部长篇小说项目，例如玄幻、都市、科幻、悬疑等。
```

---

## 3.2 章节表

```sql id="gq12dn"
novel_chapters
- id
- project_id
- title
- chapter_index
- outline
- draft_content
- final_content
- word_count
- status
- created_at
- updated_at
```

章节状态：

```text id="9g14ey"
outline
drafting
reviewing
finalized
archived
```

---

## 3.3 人物卡表

```sql id="d5smoo"
novel_characters
- id
- project_id
- name
- aliases
- role
- personality
- background
- goals
- relationships
- speech_style
- appearance
- notes
- created_at
- updated_at
```

---

## 3.4 世界观设定表

```sql id="px1wgw"
novel_world_entries
- id
- project_id
- category
- title
- content
- tags
- priority
- created_at
- updated_at
```

category 示例：

```text id="qtubp7"
世界规则
势力
地名
修炼体系
科技体系
历史事件
关键道具
伏笔
禁忌
```

---

## 3.5 Prompt 模板表

```sql id="8u0rpk"
prompt_templates
- id
- name
- type
- system_prompt
- instruction_template
- negative_prompt
- variables_schema
- output_constraints
- created_at
- updated_at
```

type 示例：

```text id="2ldauc"
chapter_generate
chapter_continue
chapter_rewrite
dialogue_enhance
scene_expand
style_polish
outline_generate
character_generate
```

---

## 3.6 生成记录表

```sql id="fitkp0"
generation_records
- id
- project_id
- chapter_id
- template_id
- model_id
- adapter_id
- prompt_rendered
- input_context
- model_output
- generation_params
- status
- created_at
```

generation_params 包含：

```json id="2km4d6"
{
  "max_tokens": 2048,
  "temperature": 0.8,
  "top_p": 0.9,
  "repetition_penalty": 1.1,
  "stream": true
}
```

---

## 3.7 人工修订表

```sql id="6qx288"
revision_records
- id
- generation_id
- project_id
- chapter_id
- original_text
- edited_text
- diff_json
- edit_tags
- user_score
- accepted_for_dataset
- created_at
```

edit_tags 示例：

```text id="qb1oq2"
语言润色
剧情修正
人物性格增强
对白优化
节奏调整
细节补充
减少废话
文风统一
逻辑修复
```

---

## 3.8 数据集表

```sql id="o1ypf0"
training_datasets
- id
- name
- type
- description
- sample_count
- status
- export_path
- created_at
- updated_at
```

type：

```text id="1ytpn7"
sft
preference
mixed
```

---

## 3.9 数据样本表

```sql id="jw0h1q"
training_samples
- id
- dataset_id
- project_id
- revision_id
- sample_type
- instruction
- input
- output
- chosen
- rejected
- metadata_json
- quality_score
- status
- created_at
```

---

## 3.10 微调任务表

```sql id="pf4cxx"
finetune_jobs
- id
- dataset_id
- base_model_id
- method
- adapter_name
- training_config
- job_id
- status
- output_adapter_path
- metrics_json
- created_at
- updated_at
```

method：

```text id="nx2pdi"
lora
qlora
```

---

# 4. API 设计

## 4.1 小说项目 API

```text id="4yq6ja"
GET    /v1/novels/projects
POST   /v1/novels/projects
GET    /v1/novels/projects/{project_id}
PATCH  /v1/novels/projects/{project_id}
DELETE /v1/novels/projects/{project_id}
```

---

## 4.2 章节 API

```text id="030xqx"
GET    /v1/novels/projects/{project_id}/chapters
POST   /v1/novels/projects/{project_id}/chapters
GET    /v1/novels/chapters/{chapter_id}
PATCH  /v1/novels/chapters/{chapter_id}
DELETE /v1/novels/chapters/{chapter_id}
```

---

## 4.3 人物与世界观 API

```text id="p0k3m3"
GET    /v1/novels/projects/{project_id}/characters
POST   /v1/novels/projects/{project_id}/characters
PATCH  /v1/novels/characters/{character_id}
DELETE /v1/novels/characters/{character_id}

GET    /v1/novels/projects/{project_id}/world
POST   /v1/novels/projects/{project_id}/world
PATCH  /v1/novels/world/{entry_id}
DELETE /v1/novels/world/{entry_id}
```

---

## 4.4 Prompt 模板 API

```text id="gxg4m3"
GET    /v1/prompts/templates
POST   /v1/prompts/templates
GET    /v1/prompts/templates/{template_id}
PATCH  /v1/prompts/templates/{template_id}
DELETE /v1/prompts/templates/{template_id}

POST   /v1/prompts/render
```

`/v1/prompts/render` 用于预览最终 Prompt。

---

## 4.5 写作生成 API

```text id="c1kzrp"
POST /v1/writing/generate
POST /v1/writing/stream
POST /v1/writing/rewrite
POST /v1/writing/continue
POST /v1/writing/polish
POST /v1/writing/expand
POST /v1/writing/summarize
```

请求示例：

```json id="9xkixp"
{
  "project_id": "project-001",
  "chapter_id": "chapter-001",
  "template_id": "template-chapter-generate",
  "model_id": "qwen-local",
  "adapter_id": null,
  "mode": "chapter_continue",
  "target_length": {
    "unit": "words",
    "min": 1200,
    "max": 1800
  },
  "variables": {
    "chapter_goal": "主角进入黑市，第一次发现灵骨交易。",
    "style": "紧张、压迫、细节丰富",
    "pov": "第三人称"
  },
  "generation_params": {
    "temperature": 0.8,
    "top_p": 0.9,
    "max_tokens": 2048
  }
}
```

---

## 4.6 修订 API

```text id="t61p77"
POST /v1/revisions
GET  /v1/revisions
GET  /v1/revisions/{revision_id}
POST /v1/revisions/{revision_id}/accept
POST /v1/revisions/{revision_id}/reject
POST /v1/revisions/{revision_id}/to-sample
```

---

## 4.7 数据集 API

```text id="h6e4dm"
GET    /v1/datasets
POST   /v1/datasets
GET    /v1/datasets/{dataset_id}
POST   /v1/datasets/{dataset_id}/add-samples
POST   /v1/datasets/{dataset_id}/export
DELETE /v1/datasets/{dataset_id}
```

导出格式：

```text id="19opqw"
SFT JSONL
Preference JSONL
Alpaca JSONL
ChatML JSONL
```

---

## 4.8 微调 API

```text id="zeluej"
POST /v1/finetune/jobs
GET  /v1/finetune/jobs
GET  /v1/finetune/jobs/{job_id}
POST /v1/finetune/jobs/{job_id}/cancel
GET  /v1/finetune/jobs/{job_id}/logs
```

微调任务复用现有：

```text id="bx916o"
JobQueue
GPU Scheduler
Adapter Manager
Storage
Diagnostics
```

---

# 5. Prompt 系统设计

## 5.1 Prompt 模板结构

每个模板由以下部分组成：

```text id="c92bqz"
system_prompt
role_prompt
world_context
character_context
chapter_context
previous_context
writing_instruction
output_constraints
negative_prompt
```

---

## 5.2 Prompt 变量

支持变量：

```text id="exxoh7"
{{project_title}}
{{genre}}
{{world_setting}}
{{characters}}
{{chapter_outline}}
{{previous_chapter_summary}}
{{current_chapter_goal}}
{{target_length}}
{{style}}
{{pov}}
{{forbidden_content}}
{{user_instruction}}
```

---

## 5.3 小说生成模板示例

```text id="kivzgy"
你是一名专业网络小说作者，擅长长篇连载小说创作。

小说类型：
{{genre}}

世界观设定：
{{world_setting}}

主要人物：
{{characters}}

上一章摘要：
{{previous_chapter_summary}}

当前章节目标：
{{current_chapter_goal}}

写作要求：
1. 使用 {{pov}}。
2. 字数控制在 {{target_length}}。
3. 风格要求：{{style}}。
4. 保持人物性格一致。
5. 不要跳过关键情节。
6. 不要直接总结剧情，要写成正文。
7. 避免重复、空泛和流水账。

请输出当前章节正文。
```

---

# 6. 写作工作流设计

## 6.1 章节生成流程

```text id="3dlqni"
1. 用户选择小说项目。
2. 用户选择章节。
3. 用户选择 Prompt 模板。
4. 用户填写章节目标。
5. 系统自动收集：
   - 世界观
   - 人物卡
   - 上一章摘要
   - 当前章节大纲
   - 已写正文上下文
6. PromptRenderer 渲染最终 Prompt。
7. 用户可以预览 Prompt。
8. 调用本地模型生成。
9. 流式返回正文。
10. 用户选择接受、重写、继续、人工修改。
```

---

## 6.2 人工修改流程

```text id="5st1w1"
1. 模型生成一版正文。
2. 用户在编辑器中修改。
3. 系统自动保存原文和修改后文本。
4. 系统生成 diff。
5. 用户选择修改标签。
6. 用户评分。
7. 用户选择是否加入训练数据。
```

---

## 6.3 反哺模型流程

```text id="1sg8wd"
1. 从 revision_records 中筛选高质量修改。
2. 构建 SFT 样本。
3. 用户审核样本。
4. 导出 JSONL。
5. 启动 LoRA / QLoRA 微调。
6. 训练完成生成 Adapter。
7. Adapter 注册到现有 AdapterManager。
8. 用户加载 Adapter 再次写作。
9. 对比微调前后效果。
```

---

# 7. 数据集构建设计

## 7.1 SFT 样本

适合训练模型直接输出更好的小说正文。

```json id="08oo64"
{
  "instruction": "根据世界观、人物设定和章节目标续写小说正文。",
  "input": "世界观：...\n人物：...\n上一章摘要：...\n章节目标：...",
  "output": "人工修改后的最终正文。"
}
```

---

## 7.2 Preference 样本

适合后续 DPO / 偏好训练。

```json id="yxakm7"
{
  "prompt": "根据以下设定续写小说正文：...",
  "chosen": "人工修改后的版本",
  "rejected": "模型原始版本"
}
```

---

## 7.3 样本审核状态

```text id="bfcz24"
pending
approved
rejected
exported
```

第一阶段只做：

```text id="0p4gyf"
SFT JSONL 导出
```

后续再做：

```text id="iy37f9"
Preference JSONL
DPO 数据
自动质量评分
重复样本清理
```

---

# 8. 微调设计

## 8.1 第一阶段策略

第一阶段只支持：

```text id="qwxz88"
LoRA / QLoRA
```

不做全量微调。

原因：

```text id="1te72d"
1. 成本低。
2. 可回滚。
3. 可以按小说项目或作者风格生成多个 Adapter。
4. 和现有 AdapterManager 可以复用。
```

---

## 8.2 训练参数

基础参数：

```json id="9lj649"
{
  "method": "qlora",
  "base_model_id": "qwen-local",
  "dataset_id": "dataset-001",
  "adapter_name": "my-novel-style-v1",
  "epochs": 3,
  "learning_rate": 0.0002,
  "lora_rank": 16,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "batch_size": 1,
  "gradient_accumulation_steps": 8,
  "max_seq_length": 4096
}
```

---

## 8.3 微调输出

训练完成后输出：

```text id="chj17c"
data/adapters/{adapter_name}/
├── adapter_config.json
├── adapter_model.safetensors
├── training_config.json
├── metrics.json
└── dataset_snapshot.json
```

然后自动注册到：

```text id="rtjvwc"
AdapterManager
```

---

# 9. Flutter 页面设计

## 9.1 Novel Projects 页面

功能：

```text id="w0rxfe"
1. 新建小说项目。
2. 查看项目列表。
3. 设置小说类型、目标风格、简介。
4. 进入写作工作台。
```

---

## 9.2 Prompt Studio 页面

功能：

```text id="idzreb"
1. 创建 Prompt 模板。
2. 编辑 system_prompt。
3. 编辑 instruction_template。
4. 配置变量。
5. 预览最终 Prompt。
6. 保存模板。
```

---

## 9.3 Writing Workspace 页面

布局建议：

```text id="4y6f6s"
左侧：
  项目章节列表
  人物卡
  世界观卡

中间：
  正文编辑器
  模型输出区
  人工修改区

右侧：
  Prompt 模板
  生成参数
  模型选择
  Adapter 选择
  字数控制
  生成按钮

底部：
  Diff
  生成日志
  保存为训练样本
```

核心按钮：

```text id="b2dhtz"
生成
续写
重写
润色
扩写
停止
保存
保存为训练样本
```

---

## 9.4 Revision Review 页面

功能：

```text id="fby6wq"
1. 查看模型原文。
2. 查看人工修改后文本。
3. 查看 diff。
4. 添加修改标签。
5. 用户评分。
6. 加入数据集。
```

---

## 9.5 Dataset Builder 页面

功能：

```text id="x7pjk1"
1. 查看训练样本列表。
2. 筛选项目、章节、标签、评分。
3. 审核样本。
4. 导出 JSONL。
5. 查看导出路径。
```

---

## 9.6 Fine-tune Center 页面

功能：

```text id="q2g4my"
1. 选择基础模型。
2. 选择数据集。
3. 配置 LoRA 参数。
4. 启动训练任务。
5. 查看训练日志。
6. 查看 loss。
7. 训练完成后注册 Adapter。
```

---

# 10. 权限与安全

## 10.1 权限建议

```text id="bdq8cm"
viewer:
  只能查看项目、章节、生成结果。

operator:
  可以生成、编辑、保存 revision、导出数据集。

admin:
  可以删除项目、启动微调、管理 Adapter、清理数据。
```

---

## 10.2 数据安全

必须避免：

```text id="d825b3"
1. API Key 写入日志。
2. 模型路径泄露给低权限用户。
3. 训练数据误删。
4. 微调任务覆盖已有 Adapter。
5. 未审核样本直接进入训练。
```

---

# 11. 文件目录设计

```text id="kdd7do"
data/
├── novels/
│   └── {project_id}/
│       ├── chapters/
│       ├── exports/
│       └── assets/
├── datasets/
│   └── {dataset_id}/
│       ├── train.jsonl
│       ├── val.jsonl
│       └── metadata.json
├── adapters/
│   └── {adapter_name}/
├── finetune/
│   └── jobs/
└── logs/
```

---

# 12. 分阶段开发计划

## 阶段 1：Novel 项目与章节基础

目标：

```text id="hzwuws"
搭建小说项目、章节、人物、世界观的基础数据结构。
```

开发内容：

```text id="aalbvk"
1. 新增 novels 模块。
2. 新增 SQLite 表。
3. 新增 NovelProjectRepository。
4. 新增 ChapterRepository。
5. 新增 CharacterRepository。
6. 新增 WorldEntryRepository。
7. 新增项目和章节 API。
8. Flutter 新增 Novel Projects 页面。
9. Flutter 新增章节列表和基础编辑页面。
```

验收：

```text id="tjj3fi"
1. 可以创建小说项目。
2. 可以创建章节。
3. 可以保存章节草稿。
4. 可以添加人物卡。
5. 可以添加世界观设定。
```

---

## 阶段 2：Prompt Studio 模板系统

目标：

```text id="vivhl2"
建立可复用的 Prompt 模板系统。
```

开发内容：

```text id="qedvkj"
1. 新增 prompts 模块。
2. 新增 PromptTemplateRepository。
3. 新增 PromptRenderer。
4. 支持变量占位符。
5. 支持模板预览。
6. 提供默认模板：
   - 章节生成
   - 章节续写
   - 润色
   - 扩写
   - 对白增强
7. Flutter 新增 Prompt Studio 页面。
```

验收：

```text id="rz4n80"
1. 可以创建 Prompt 模板。
2. 可以填充变量。
3. 可以预览最终 Prompt。
4. 可以在章节生成时选择模板。
```

---

## 阶段 3：本地小说生成闭环

目标：

```text id="4pwu5t"
复用现有本地模型 Runtime 生成小说内容。
```

开发内容：

```text id="qwz19o"
1. 新增 writing 模块。
2. 新增 WritingService。
3. 接入 ModelRepository。
4. 接入 Runtime.generate。
5. 接入 Runtime.stream。
6. 支持 max_tokens、temperature、top_p。
7. 支持目标字数配置。
8. 支持生成、续写、重写、润色、扩写。
9. Flutter Writing Workspace 接入流式输出。
```

验收：

```text id="349r1t"
1. 可以选择本地模型。
2. 可以选择 Prompt 模板。
3. 可以生成小说正文。
4. 可以流式输出。
5. 可以停止生成。
6. 可以保存生成结果到章节。
```

---

## 阶段 4：人工修改与 Revision 系统

目标：

```text id="1nbi6d"
将模型输出和人工修改保存下来。
```

开发内容：

```text id="n2wgg4"
1. 新增 revisions 模块。
2. 新增 RevisionRepository。
3. 保存 original_text。
4. 保存 edited_text。
5. 生成 diff_json。
6. 支持修改标签。
7. 支持用户评分。
8. Flutter 支持原文 / 修改后 / Diff 对比。
```

验收：

```text id="zmye8f"
1. 模型生成后可以人工编辑。
2. 可以保存修订记录。
3. 可以查看 diff。
4. 可以给修改打标签。
5. 可以评分。
```

---

## 阶段 5：Dataset Builder 数据集构建

目标：

```text id="2dbp37"
把人工修改记录转换为可训练数据。
```

开发内容：

```text id="hgl8x9"
1. 新增 datasets 模块。
2. 支持从 revision 生成 SFT 样本。
3. 支持人工审核样本。
4. 支持导出 SFT JSONL。
5. 支持样本质量评分。
6. Flutter 新增 Dataset Builder 页面。
```

验收：

```text id="ydx69y"
1. 可以选择 revision 加入数据集。
2. 可以审核训练样本。
3. 可以导出 train.jsonl。
4. 导出的 JSONL 可以被训练脚本读取。
```

---

## 阶段 6：LoRA / QLoRA 微调中心

目标：

```text id="x9kbhc"
使用数据集对本地模型做 LoRA / QLoRA 微调。
```

开发内容：

```text id="aa2eu1"
1. 新增 finetune 模块。
2. 接入 JobQueue。
3. 接入 GPU Scheduler。
4. 支持 LoRA 参数配置。
5. 支持 QLoRA 参数配置。
6. 支持训练日志。
7. 支持训练结果 Adapter 注册。
8. Flutter 新增 Fine-tune Center 页面。
```

验收：

```text id="m1g0sx"
1. 可以选择数据集。
2. 可以选择基础模型。
3. 可以启动 LoRA 训练任务。
4. 可以查看训练日志。
5. 训练完成后 Adapter 出现在 Adapter 页面。
6. 可以加载 Adapter 重新生成小说。
```

---

## 阶段 7：小说上下文记忆与 RAG 增强

目标：

```text id="cs9f7c"
解决长篇小说上下文遗忘问题。
```

开发内容：

```text id="2vleiz"
1. 将章节摘要写入 Memory。
2. 将人物卡、世界观写入 RAG。
3. 生成时自动检索相关设定。
4. 支持上下文预算管理。
5. 支持章节摘要自动更新。
```

验收：

```text id="y36y71"
1. 长篇生成时能引用已有设定。
2. 人物关系不容易遗忘。
3. 章节之间剧情更连贯。
4. Prompt 不会无限膨胀。
```

---

## 阶段 8：评估中心

目标：

```text id="ee4xeq"
评估生成质量和微调效果。
```

开发内容：

```text id="gxwy0a"
1. 风格一致性评估。
2. 人物一致性评估。
3. 剧情连贯性评估。
4. 重复率检测。
5. 人工评分。
6. 微调前后对比。
```

验收：

```text id="qwo8nw"
1. 可以比较基础模型和微调 Adapter。
2. 可以生成评估报告。
3. 可以人工打分。
4. 可以筛选高质量样本继续训练。
```

---

## 阶段 9：UI 产品化

目标：

```text id="hoxsxa"
把 Novel Studio 做成可长期使用的写作工作台。
```

开发内容：

```text id="gxhrai"
1. 项目导航。
2. 章节树。
3. 富文本编辑器。
4. Diff 视图。
5. 训练数据审核表格。
6. 任务状态栏。
7. 错误提示统一。
8. 深色 / 浅色主题。
```

验收：

```text id="cqqi9v"
1. 用户可以完整写一章小说。
2. 用户可以修改并保存。
3. 用户可以构建数据集。
4. 用户可以启动微调。
5. 用户可以加载微调结果继续创作。
```

---

## 阶段 10：发布与打包

目标：

```text id="1i6aws"
形成可交付 Windows 桌面版本。
```

开发内容：

```text id="jyn7d8"
1. Windows 桌面构建。
2. 后端启动脚本。
3. 数据目录初始化。
4. 用户文档。
5. 诊断包。
6. 错误日志。
7. 版本升级说明。
```

验收：

```text id="i8et6v"
1. Windows 11 可运行。
2. 首次启动能初始化。
3. 能加载本地模型。
4. 能创作小说。
5. 能导出训练数据。
6. 能执行微调任务。
```

---

# 13. 推荐开发顺序

建议严格按下面顺序推进：

```text id="ksccz6"
1. Novel 项目与章节基础。
2. Prompt Studio 模板系统。
3. 本地小说生成闭环。
4. 人工修改与 Revision 系统。
5. Dataset Builder 数据集构建。
6. LoRA / QLoRA 微调中心。
7. 小说上下文记忆与 RAG 增强。
8. Evaluation Center。
9. UI 产品化。
10. Windows 发布与验收。
```

不要一开始就做微调。最关键的是先把：

```text id="s4zw0s"
生成 → 人工修改 → 数据沉淀
```

这个闭环打通。

---

# 14. 第一阶段最小可用版本

第一版 MVP 推荐只做：

```text id="veith3"
1. 创建小说项目。
2. 创建章节。
3. 创建 Prompt 模板。
4. 选择本地模型。
5. 生成章节内容。
6. 人工编辑。
7. 保存 revision。
8. 导出 SFT JSONL。
```

这个版本已经可以验证产品核心价值：

```text id="l8f41d"
本地模型是否能辅助写小说；
Prompt 是否能控制风格；
人工修改是否能沉淀成可训练数据。
```

---

# 15. 下一步落地建议

下一步可以直接进入：

```text id="neimj5"
阶段 1：Novel 项目与章节基础
```

优先开发：

```text id="sbo4ip"
1. llm_studio/novels 模块。
2. SQLite 表。
3. 小说项目 API。
4. 章节 API。
5. Flutter Novel Projects 页面。
6. Flutter Chapter Editor 页面。
```

等阶段 1 完成后，再做 Prompt Studio。这样开发风险最低，也最容易验收。
