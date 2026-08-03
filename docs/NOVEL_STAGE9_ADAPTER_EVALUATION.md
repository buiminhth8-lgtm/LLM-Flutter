# Novel Studio Stage 9: Adapter Evaluation and Generation Comparison

Stage 9 consumes completed Stage 8 adapters and lets users compare a base model
against a selected Adapter on the same Novel Studio prompt/context snapshot.
The result is a manual review asset: users score outputs, pick a winner, create
a lightweight report, and may explicitly hand a selected result to Stage 5
Revision.

## Scope

- Create `/v1/adapter-evaluations/*` APIs.
- Persist evaluation sessions, frozen cases, base/adapter results, manual
  scores, and reports.
- Reuse Stage 3 `ContextAssembler`, Stage 2 `PromptRenderer`, and Stage 4
  `WritingRuntimeBridge`.
- Compare base model and Adapter using the same rendered prompt and generation
  parameters.
- Save manual score dimensions, winner, reviewer notes, and report summaries.
- Support explicit Revision creation from a selected evaluation result.
- Add Flutter Adapter Evaluation pages and a completed Fine-tune Run entry.

## Boundaries

Stage 9 is not a full automatic evaluation platform.

It does not include:

- automatic style consistency scoring;
- automatic character consistency scoring;
- automatic plot coherence scoring;
- RAG, vector search, embeddings, or memory;
- DPO, RLHF, preference optimization, or reinforcement learning;
- LoRA/QLoRA training;
- automatic adapter activation;
- automatic creation of `training_samples`;
- automatic promotion of generated text into datasets.

## Data model

### adapter_evaluation_sessions

Session-level metadata for a base-vs-adapter comparison batch.

Important fields:

- `project_id`: optional project scope.
- `finetune_run_id`: optional Stage 8 run reference.
- `dataset_version_id`: optional frozen DatasetVersion reference used by the
  run or reviewer.
- `base_model_id`: model used without Adapter.
- `adapter_id`: Adapter under review.
- `status`: `draft`, `ready`, `running`, `reviewing`, `completed`, `archived`,
  or `failed`.
- `stats_json`: aggregated counts and last report summary.

### adapter_evaluation_cases

Frozen prompt/context cases. A case records the exact rendered prompt,
context snapshot, generation parameters, and target length used for both
variants.

Important fields:

- `prompt_rendered`: prompt produced by `PromptRenderer`.
- `context_snapshot_json`: output from context assembly.
- `generation_params_json`: decoding parameters reused for base and adapter.
- `target_length_json`: Chinese-length target metadata.
- `prompt_hash` and `context_hash`: SHA-256 hashes for auditability.

### adapter_evaluation_results

One result per variant (`base`, `adapter`) for each case.

Important fields:

- `variant`: `base` or `adapter`.
- `model_id`: base model id.
- `adapter_id`: null for `base`, selected Adapter for `adapter`.
- `output_text`: generated output.
- `status`: `succeeded` or `failed`.
- `output_hash`, `output_char_count`, `output_token_estimate`, `latency_ms`.
- `error_code`, `error_message`: sanitized failure data for partial failures.

### adapter_evaluation_scores

Manual review data. Scores are intentionally human-supplied only.

Supported winner values:

- `base`
- `adapter`
- `tie`
- `none`

Scores are optional but, when present, must be integers from 1 to 5.

Supported score dimensions:

- `style`
- `language_quality`
- `character_consistency`
- `plot_coherence`
- `worldbuilding`
- `dialogue`
- `pacing`
- `overall`

### adapter_evaluation_reports

Reports aggregate manual scores. The report builder summarizes win counts,
average base/adapter scores, warnings, and a recommendation such as
`adapter_candidate`, `needs_more_cases`, `needs_human_review`, or
`keep_base`.

## Service flow

### Create session

`AdapterEvaluationService.create_session(...)` validates:

1. base model exists;
2. adapter exists and is compatible with the base model;
3. optional project exists;
4. optional DatasetVersion exists;
5. optional Fine-tune Run exists, is `completed`, and references the same
   base model / adapter when those fields are present.

### Create or prepare case

`create_case(...)` and `prepare_case(...)` assemble context and render the
prompt through existing Novel Studio services. The rendered prompt is then
frozen in `adapter_evaluation_cases`; later runs reuse that frozen prompt.

### Run comparison

`run_case(...)` invokes `AdapterComparisonRunner`, which calls
`WritingRuntimeBridge.generate_text(...)` twice:

1. base variant: `adapter_id=None`;
2. adapter variant: `adapter_id=session.adapter_id`.

Both results are persisted. If one side fails, the other result remains saved
and the failure is stored on the failed result. If both sides fail, the case is
marked `failed`.

`run_session(...)` is a bounded synchronous runner for the initial Stage 9 UI.
It prepares pending cases and runs up to a safe case limit. A later stage can
move long evaluation batches into JobQueue if needed.

### Manual scoring

`score_case(...)` requires a completed pair and stores the reviewer’s winner,
score values, dimension scores, and notes.

### Report

`generate_report(...)` reads stored cases, results, and manual scores. It does
not call any model and does not run automatic evaluators.

### Revision handoff

`create_revision_from_result(...)` creates a Stage 5 Revision only when the user
explicitly selects a successful result. The default original text is the base
output and the edited text is the selected result. The created Revision has
`source=adapter_evaluation` and does not create training samples.

## API examples

Create a session:

```json
POST /v1/adapter-evaluations/sessions
{
  "name": "Qwen adapter smoke comparison",
  "project_id": "project-001",
  "finetune_run_id": "run-001",
  "dataset_version_id": "dsv-001",
  "base_model_id": "qwen-local",
  "adapter_id": "adapter-001"
}
```

Create a case:

```json
POST /v1/adapter-evaluations/sessions/session-001/cases
{
  "title": "Chapter 3 continuation",
  "project_id": "project-001",
  "chapter_id": "chapter-003",
  "template_id": "template-continue",
  "mode": "chapter_continue",
  "user_variables": {
    "current_chapter_goal": "主角第一次识破黑市交易。",
    "style": "紧张、细节丰富",
    "pov": "第三人称"
  },
  "generation_params": {
    "temperature": 0.8,
    "top_p": 0.9,
    "max_tokens": 768
  }
}
```

Run a case:

```json
POST /v1/adapter-evaluations/cases/case-001/run
{}
```

Score a case:

```json
POST /v1/adapter-evaluations/cases/case-001/score
{
  "winner": "adapter",
  "base_score": 3,
  "adapter_score": 5,
  "dimensions": {
    "style": {"base": 3, "adapter": 5},
    "overall": {"base": 3, "adapter": 5}
  },
  "notes": "Adapter 输出更贴近目标文风。"
}
```

Generate a report:

```json
POST /v1/adapter-evaluations/sessions/session-001/report
{}
```

Create Revision from an evaluation result:

```json
POST /v1/adapter-evaluations/results/result-adapter/create-revision
{
  "project_id": "project-001",
  "chapter_id": "chapter-003",
  "source_original": "base",
  "edit_tags": ["style_unify"],
  "user_score": 4,
  "quality_notes": "Adapter 输出作为人工修订候选。"
}
```

## Flutter Adapter Evaluation UI

Flutter adds:

- Adapter Evaluation navigation entry when `adapter_evaluation=available`.
- Session list page.
- Session detail page.
- Case creation dialog.
- Base-vs-Adapter compare page.
- Manual score panel.
- Report panel.
- Revision handoff button.
- Fine-tune Run Detail button for completed runs with a registered Adapter.

The UI intentionally avoids training buttons, JSONL export controls, automatic
evaluation controls, or adapter activation actions in Stage 9.

## Capabilities

When Novel Studio and Adapter Evaluation flags are enabled:

- `adapter_evaluation`: `available`
- `adapter_base_compare`: `available`
- `adapter_manual_scoring`: `available`
- `adapter_evaluation_report`: `available`

Still not implemented:

- `full_evaluation_center`
- `novel_rag_memory`
- `novel_evaluation`

## Stage 10 prerequisites

- Completed Adapter Evaluation sessions and reports.
- Clear manual comparison evidence for which Adapter is worth continued use.
- No dependency on automatic RAG/Memory or Evaluation Center features.
