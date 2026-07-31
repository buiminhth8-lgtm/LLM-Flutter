# Novel Studio 阶段 5：Revision 人工修订与版本系统

Stage 5 builds a human revision layer on top of Stage 4 Writing. It records the
model original text, the human edited text, backend-generated diff data, review
metadata, autosaves, and a future Dataset Builder candidate flag.

## 范围

- 新增 `llm_studio/revisions` 后端模块。
- 新增 `revision_records` 与 `revision_autosaves` SQLite 表。
- 新增 `/v1/revisions/*` API。
- Flutter 新增 `Revision Review` 页面、revision list、editor、Diff View、tag/score/status/candidate controls。
- Writing Workspace 的 generation history 增加 `Create Revision` / `View Revision`，AI 输出区增加 `Edit as Revision`。

Stage 5 does not call Runtime, generate new text, train models, export JSONL, or
create dataset/training records.

## RevisionRecord 字段

| 字段 | 含义 |
| --- | --- |
| `id` / `revision_id` | revision 主键；API 返回 `revision_id` |
| `generation_id` | 可为空；从 Stage 4 generation 创建时关联 `generation_records.id` |
| `project_id` / `chapter_id` / `scene_id` | Novel 资料关联 |
| `original_text` | 模型输出或修订前文本 |
| `edited_text` | 人工修改后的文本 |
| `diff_json` | 后端生成并持久化的 diff |
| `edit_tags_json` | 修改标签数组 |
| `user_score` | 可为空；设置时必须为 1 到 5 |
| `quality_notes` | 人工质量备注 |
| `status` | `draft`、`reviewing`、`approved`、`rejected`、`archived` |
| `accepted_for_dataset` | Stage 6 候选标记，不创建训练样本 |
| `reviewer_id` | 审核人标识，可为空 |
| `source` | `generation`、`chapter_draft`、`manual` |
| `original_hash` / `edited_hash` | SHA-256 |
| `created_at` / `updated_at` | UTC ISO 时间 |

## Revision 与 Generation

`POST /v1/revisions/from-generation` 读取
`generation_records.model_output` 作为 `original_text`。如果请求没有传
`edited_text`，后端会用 original 初始化人工稿。Revision 不会修改 Stage 4
generation record，也不会把 `Save to Draft` 视为 revision。

## Revision 与 Dataset 的边界

`accepted_for_dataset` 只是候选布尔值，用于 Stage 6 Dataset Builder 选择素材。
Stage 5 不创建 Dataset Builder、`training_samples`、SFT JSONL、Preference
Dataset、FineTune、Evaluation 或任何训练任务。

低分 revision 仍可被人工标记为候选，但当 `user_score < 4` 且
`accepted_for_dataset=true` 时，API 返回 warning。

## diff_json 格式

后端使用 Python 标准库 `difflib`，短文本按字符 diff，长文本或多行文本按行
diff，输出稳定 JSON：

```json
{
  "format": "line_word_v1",
  "summary": {
    "original_chars": 1200,
    "edited_chars": 1350,
    "added_chars": 240,
    "removed_chars": 90,
    "changed_blocks": 12
  },
  "ops": [
    {"type": "equal", "text": "夜色沉入旧城。"},
    {"type": "delete", "text": "他很紧张。"},
    {"type": "insert", "text": "他的指节微微发白，却没有后退。"}
  ]
}
```

## edit_tags

支持标签：`language_polish`、`plot_fix`、`character_consistency`、
`dialogue_improve`、`pacing_adjust`、`detail_expand`、`remove_redundancy`、
`style_unify`、`logic_fix`、`worldbuilding_fix`、`emotion_enhance`、
`scene_atmosphere`、`continuity_fix`、`other`。

未知标签返回 `REVISION_INVALID_TAG`。

## user_score

`user_score` 可为空；设置时必须为 1 到 5。`4` 和 `5` 更适合作为未来数据集候选。
范围外评分返回 `REVISION_INVALID_SCORE`。

## autosave

`revision_autosaves` 保存编辑过程中的草稿，避免长文本丢失。Autosave 不更新
`revision_records.edited_text`，不进入 Dataset，支持 `revision_id` 为空的临时编辑，
默认每个 revision 保留最近 20 条，可通过 `revisions.autosave_retention` 调整。

Flutter 编辑器在文本变化后 debounce 约 4 秒自动保存，关闭页面前尝试 flush。

## API

- `GET /v1/revisions`
- `GET /v1/revisions/{revision_id}`
- `PATCH /v1/revisions/{revision_id}`
- `DELETE /v1/revisions/{revision_id}`
- `POST /v1/revisions/from-generation`
- `POST /v1/revisions/from-chapter-draft`
- `POST /v1/revisions/manual`
- `POST /v1/revisions/{revision_id}/approve`
- `POST /v1/revisions/{revision_id}/reject`
- `POST /v1/revisions/{revision_id}/dataset-candidate`
- `POST /v1/revisions/autosave`
- `GET /v1/revisions/{revision_id}/autosaves`

Create from generation:

```json
{
  "generation_id": "gen-001",
  "edited_text": "人工修改后的正文……",
  "edit_tags": ["language_polish", "detail_expand"],
  "user_score": 4,
  "quality_notes": "补充了动作细节，删除了重复描写。",
  "accepted_for_dataset": true
}
```

Optimistic locking:

```json
{
  "edited_text": "……",
  "expected_updated_at": "2026-07-30T10:00:00Z"
}
```

If `expected_updated_at` differs from the stored value, the API returns
`REVISION_CONFLICT`.

## Flutter Revision Review

The page is a three-column workbench:

- Left: revision list with project, chapter, status, and score filters.
- Center: model original, human editor, and backend diff view.
- Right: tags, score, notes, status badge, dataset candidate toggle, save, approve, and reject.

Diff View shows equal/insert/delete operations with different markers and summary
stats for changed blocks and character counts.

## Feature flag、权限与 capabilities

`features.novel_studio.enabled=false` disables `/v1/revisions/*` with
`REVISION_FEATURE_DISABLED`. `features.revision_system.enabled=false` can also
disable Stage 5 while keeping earlier Novel Studio stages available.

Initial RBAC uses project roles: viewer reads revisions, operator creates and
updates revisions, and admin can perform every revision operation.

Capabilities when enabled:

- `revision_system=AVAILABLE`
- `revision_diff=AVAILABLE`
- `revision_autosave=AVAILABLE`
- `dataset_builder=NOT_IMPLEMENTED`
- `finetune_center=NOT_IMPLEMENTED`
- `novel_rag_memory=NOT_IMPLEMENTED`
- `novel_evaluation=NOT_IMPLEMENTED`

## 阶段 6 前置条件

Stage 6 Dataset Builder can consume only explicit candidates from
`revision_records.accepted_for_dataset`. It must still validate score, status,
project boundaries, and export format, and it must not treat Stage 5 autosaves or
raw generation records as training samples by default.
