# Novel Studio Stage 11: Evaluation Center

Stage 11 adds the full Evaluation Center on top of Stage 1-10 Novel Studio
assets. It is an advisory review layer: it reads existing novel, writing,
revision, memory and adapter-evaluation records, computes automatic metrics,
stores findings, accepts manual scores, and generates reports.

It does not rewrite novel content, create training samples, freeze datasets,
start fine-tuning, activate adapters, call cloud judges, or package Windows
installers.

## Scope

Implemented in this stage:

- persistent `evaluation_runs`, `evaluation_cases`, `evaluation_metrics`,
  `evaluation_findings`, `evaluation_reports`, and `manual_evaluation_scores`;
- heuristic evaluators for repetition, style consistency, character
  consistency, world consistency, plot coherence, pacing, memory usage, and
  foreshadowing;
- optional local model judge through the existing local Runtime bridge;
- API routes under `/v1/evaluation`;
- Flutter Evaluation Center with run list, run creation, metrics, findings,
  manual scoring, and report viewing;
- entry points from Writing generations, Revisions, Memory retrieval records,
  and Adapter Evaluation sessions.

## EvaluationRun fields

- `target_type`: one of `project`, `chapter`, `generation`, `revision`,
  `memory_retrieval`, `adapter_eval_session`.
- `target_id`: the ID of the selected asset.
- `project_id`, `chapter_id`, `generation_id`, `revision_id`,
  `adapter_eval_session_id`, `memory_retrieval_id`: denormalized links for
  filtering and traceability.
- `evaluator_config_json`: enabled evaluator list and optional local judge
  settings.
- `overall_score`: aggregate advisory score, computed from automatic and manual
  metrics.
- `status`: `created`, `queued`, `running`, `completed`, `failed`,
  `cancelled`, or `archived`.

## Evaluators

- `repetition`: duplicate sentence/paragraph and repeated phrase signals.
- `style_consistency`: sentence length, dialogue/description ratio and POV
  shift heuristics.
- `character_consistency`: unknown speaker and simple speech-style conflicts.
- `world_consistency`: location/rule references against world entries.
- `plot_coherence`: chapter goal, plot thread and unresolved thread coverage.
- `pacing`: dialogue, description, action and long paragraph balance.
- `memory_usage`: selected memory chunks, retrieved chunks and text overlap.
- `foreshadowing`: setup/payoff clues from plot, timeline and memory records.
- `local_model_judge`: optional local model-as-judge. It uses the local Runtime
  only and returns warnings when unavailable.

## Manual evaluation

Manual scores are stored in `manual_evaluation_scores`. A reviewer may set an
overall score from 1 to 5, optional dimension scores such as `style`,
`character`, or `plot`, and freeform notes. Manual notes are also surfaced as
manual findings for report review.

## Reports

`evaluation_reports.report_json` contains:

- automatic metric summary;
- finding counts by severity/category;
- manual evaluation entries;
- target metadata;
- limitations and advisory disclaimer.

Reports are generated from persisted run data. They do not export SFT JSONL,
create DatasetVersion records, or trigger training.

## API examples

Create and run a chapter evaluation:

```json
POST /v1/evaluation/runs
{
  "name": "Chapter 3 continuity check",
  "target_type": "chapter",
  "target_id": "chapter-001",
  "evaluator_config": {
    "enabled_evaluators": [
      "repetition",
      "style_consistency",
      "character_consistency",
      "world_consistency",
      "plot_coherence",
      "pacing",
      "memory_usage",
      "foreshadowing"
    ]
  },
  "run_async": false
}
```

Add manual score:

```json
POST /v1/evaluation/runs/{run_id}/manual-score
{
  "reviewer_id": "operator",
  "overall_score": 4,
  "dimensions": {"style": 4, "plot": 3.5},
  "notes": "Good scene rhythm, but the final clue needs clearer payoff."
}
```

Generate report:

```text
POST /v1/evaluation/runs/{run_id}/report
GET  /v1/evaluation/reports/{report_id}
```

## Flutter UI

The Evaluation Center provides:

- left-side filters for project, target type and status;
- run list and run detail;
- metric cards;
- findings list with status updates (`open`, `acknowledged`, `resolved`,
  `dismissed`);
- manual scoring panel;
- report generation and report detail view.

Integrated entry points:

- Writing generation history: Evaluate generation.
- Writing output panel: Evaluate current generation.
- Revision Review: Evaluate revision.
- Adapter Evaluation: Open Full Evaluation.
- Memory Retrieval: Evaluate retrieval.

## Boundaries

Stage 11 explicitly excludes:

- Dataset Builder changes;
- DatasetVersion creation;
- `training_samples` creation;
- SFT JSONL export;
- LoRA / QLoRA training;
- Adapter activation;
- DPO / RLHF / preference optimization;
- automatic chapter draft/final content modification;
- cloud judge or API-key based external judging;
- external vector database dependency;
- TinyModelLab integration;
- Windows packaging / MSIX / installer work.

## Stage 12 prerequisites

Stage 12 can build product packaging and acceptance flows once:

- Evaluation Center tables and APIs are stable;
- Flutter Evaluation Center passes analyze/test;
- capabilities expose `full_evaluation_center=AVAILABLE`;
- packaging remains separated from training/evaluation side effects.
