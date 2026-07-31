# Novel Studio Stage 6 Dataset Builder

Stage 6 turns explicitly selected Stage 5 revision candidates into draft
training samples and draft JSONL exports.

Implemented scope:

- `training_datasets`: mutable draft dataset containers.
- `training_samples`: SFT samples by default, with preference fields reserved.
- `dataset_exports`: records draft JSONL exports under `data/datasets/{dataset_id}`.
- `DatasetService`: create/list/update/archive datasets, create samples from
  revisions, approve/reject samples, and export reviewed samples.
- `DatasetSampleBuilder`: builds SFT output from `revision_records.edited_text`;
  the sample input never contains `edited_text`.
- `DatasetJsonlExporter`: writes UTF-8 JSONL with `ensure_ascii=false` and
  returns relative export paths only.

Boundaries:

- No DatasetVersion, frozen dataset, manifest, train/val split, or training recipe.
- No LoRA / QLoRA / FineTuneRun / Adapter registration.
- No automatic conversion of every revision. Users must explicitly add a
  revision or run a filtered bulk action.
- `revision.accepted_for_dataset` is required before a sample can be created.
- `revision.status != approved` is a warning, not an automatic bypass.

## Stage 7 extension

- `dataset_versions`: immutable frozen snapshots of approved samples.
- `dataset_version_samples`: train / val / excluded membership with hashes,
  char counts, token estimates, duplicate groups, and warnings.
- `dataset_change_marks`: records when a frozen dataset becomes dirty.
- `training_recipes`: draft LoRA / QLoRA recommendations only.
- `DatasetFreezeService`: freezes `ready` or `dirty` datasets and writes
  `train.jsonl`, optional `val.jsonl`, and `manifest.json`.

Stage 7 still does not create `finetune_runs`, call GPU training code, or
register adapters.
