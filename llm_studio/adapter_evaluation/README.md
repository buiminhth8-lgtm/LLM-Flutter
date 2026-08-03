# llm_studio.adapter_evaluation

Stage 9 owns Adapter Evaluation for Novel Studio.

Implemented modules:

- `entities.py`: internal base/adapter pair result dataclasses.
- `schemas.py`: API request DTOs for sessions, cases, scoring, reports, and
  Revision handoff.
- `migrations.py`: `adapter_evaluation_sessions`,
  `adapter_evaluation_cases`, `adapter_evaluation_results`,
  `adapter_evaluation_scores`, and `adapter_evaluation_reports`.
- `repository.py`: SQLite persistence and JSON field normalization.
- `comparison_runner.py`: base-model vs adapter generation through
  `WritingRuntimeBridge`.
- `scoring.py`: manual winner and 1-5 score validation.
- `reports.py`: lightweight manual-score report builder.
- `revision_bridge.py`: explicit handoff from a selected evaluation result to
  Stage 5 Revision.
- `service.py`: AdapterEvaluationService orchestration.

Boundaries:

- Reuses Stage 3 `ContextAssembler`, Stage 2 `PromptRenderer`, and Stage 4
  `WritingRuntimeBridge`.
- Does not implement automatic quality scoring, style consistency scoring, or
  character/plot evaluators.
- Does not implement a full Evaluation Center.
- Does not start LoRA/QLoRA training and does not auto activate adapters.
- Does not create `training_samples`; Revision handoff only creates a draft
  Revision candidate.
- Does not use RAG, vector search, embeddings, DPO, or RLHF.
