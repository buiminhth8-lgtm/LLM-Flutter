# Novel Studio Stage 11 Evaluation Center

Stage 11 persists automatic and manual novel evaluation records. It reads Novel
Studio, Writing, Revision, Adapter Evaluation, and Memory records, then writes
only `evaluation_*` and `manual_evaluation_scores` data.

Boundaries:

- Does not train LoRA / QLoRA.
- Does not create DatasetVersion or training samples.
- Does not modify chapter drafts, final content, characters, world entries, or
  plot threads.
- Does not call cloud judging APIs.
- Optional local model judging reuses the existing loaded Runtime bridge and is
  advisory only.
