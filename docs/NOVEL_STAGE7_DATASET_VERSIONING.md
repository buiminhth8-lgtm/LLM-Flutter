# Novel Studio Stage 7: Dataset Versioning and Recipe Preview

Stage 7 freezes editable Stage 6 `training_datasets` into immutable
`dataset_versions`. It prepares artifacts for a later FineTune Center, but it
does not start LoRA / QLoRA, create `finetune_runs`, register adapters, or call
GPU training code.

## Scope

- Freeze `ready` or `dirty` datasets into `dataset_versions`.
- Persist `dataset_version_samples`, including `train`, `val`, and `excluded`.
- Write `train.jsonl`, optional `val.jsonl`, and `manifest.json`.
- Mark a frozen dataset as `dirty` when mutable `training_samples` change.
- Estimate characters and tokens without loading a tokenizer or model.
- Recommend draft LoRA / QLoRA training recipes.

## Dataset vs DatasetVersion

`training_datasets` remains a mutable draft container. `dataset_versions` are
immutable snapshots of approved samples plus split, hashes, paths, and warnings.
Changing samples after freeze never mutates old versions; it marks the dataset
`dirty`, and the user creates a new version.

Dataset status flow:

`draft -> reviewing -> ready -> frozen -> dirty -> frozen`

Any state can be archived. Only `ready` and `dirty` can freeze.

## Tables

- `dataset_versions`: immutable version metadata, counts, hashes, artifact paths.
- `dataset_version_samples`: sample membership, split, order, token estimates,
  duplicate group, warnings.
- `dataset_change_marks`: why a frozen/dirty dataset changed after freeze.
- `training_recipes`: draft recipe recommendations; confirmation is not a job.

## Freeze flow

1. Validate dataset exists and is `ready` or `dirty`.
2. Load approved samples.
3. Validate instruction/output fields.
4. Run exact hash dedupe.
5. Run lightweight near-duplicate warnings.
6. Split train/validation by project, chapter, sample, or no validation.
7. Estimate chars and tokens.
8. Write JSONL artifacts.
9. Write manifest.
10. Persist version and version samples.
11. Set dataset status to `frozen`.

## Dedupe

Exact dedupe uses `content_hash`; duplicates are recorded as `excluded`.
Near-duplicate detection uses normalized text and `difflib.SequenceMatcher`,
bucketed by text length. It is warning-only and can be disabled.

## Split

Default strategy is `group_by_chapter`; the same `chapter_id` is never split
between train and validation. Datasets under 10 samples use no validation and
record warnings.

## Token estimate

Stage 7 does not load a tokenizer. Chinese non-whitespace characters and
punctuation count approximately as one token. English words count about 1.3
tokens. `instruction + input + output/chosen/rejected` are counted.

## Manifest

Path:

`data/datasets/{dataset_id}/versions/v{version}/manifest.json`

The API stores and returns relative paths such as
`datasets/{dataset_id}/versions/v1/manifest.json`. Manifest includes version id,
format, split config, counts, stats, hashes, and warnings. It excludes API keys,
absolute model paths, and local absolute paths.

## TrainingRecipeRecommender

The recommender creates `training_recipes` with method, config, warnings, VRAM
estimate, and rough train-time estimate. 8GB VRAM defaults to QLoRA. Very small
datasets warn about overfitting; missing validation split warns separately.

`confirmed` means the user accepted the draft configuration. It does not start
training.

## Flutter

Dataset Builder now shows dataset status, Freeze, DatasetVersion list, manifest
summary, split summary, dedupe warnings, and Training Recipe Preview. There is
no Start Training / Run LoRA / Register Adapter action.

## Not included

- FineTuneRun
- `/v1/finetune/jobs`
- LoRA / QLoRA execution
- Adapter registration
- DPO / RLHF training
- Evaluation Center

## Stage 8 prerequisites

Stage 8 can consume confirmed recipes and immutable dataset versions, then add
FineTuneRun job orchestration, GPU scheduling, training execution boundaries,
and adapter artifact registration.
