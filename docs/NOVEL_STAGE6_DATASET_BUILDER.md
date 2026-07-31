# Novel Studio Stage 6: Dataset Builder

Stage 6 adds a draft Dataset Builder on top of Stage 5 Revision. It converts
explicitly selected `revision_records` into reviewed `training_samples` and can
export approved SFT samples as draft JSONL.

## Scope

- Create mutable `training_datasets`.
- Create `training_samples` from revisions with `accepted_for_dataset=true`.
- Support SFT samples using `instruction` / `input` / `output`.
- Reserve preference sample fields using `chosen` / `rejected`.
- Review samples with `pending`, `approved`, `rejected`, `archived`.
- Export approved SFT samples to UTF-8 JSONL under `data/datasets/`.

## Dataset and Revision relationship

Dataset Builder reads Stage 5 revisions. A revision must be explicitly marked
`accepted_for_dataset=true`; otherwise sample creation returns
`DATASET_REVISION_NOT_ACCEPTED`. If a revision is not `approved`, Stage 6 writes
a warning to sample metadata instead of silently bypassing review.

SFT construction:

- `instruction`: prompt template instruction summary when available, otherwise
  the default novel-writing instruction.
- `input`: generation `prompt_rendered` when available. `edited_text` is never
  copied into input.
- `output`: revision `edited_text`.

## Dataset vs DatasetVersion

Stage 6 datasets are drafts. They are useful for review and draft JSONL export,
but they are not immutable training artifacts.

Not included:

- DatasetVersion / frozen dataset
- train / val split
- manifest / immutable hash bundle
- exact token statistics
- TrainingRecipe
- FineTune / LoRA / QLoRA
- Adapter evaluation

If a client requests a frozen state, the backend returns
`DATASET_VERSION_NOT_IMPLEMENTED`.

## Tables

`training_datasets` stores draft dataset metadata, counts, type, and status.

`training_samples` stores SFT or preference draft samples, source revision and
generation IDs, hashes, review status, score, and metadata warnings.

`dataset_exports` stores relative export paths, format, sample count, approved
filter, export hash, and status.

## Export formats

Required Stage 6 format:

```json
{"instruction":"...","input":"...","output":"...","metadata":{"sample_id":"...","revision_id":"...","project_id":"..."}}
```

Also reserved or basic:

- `alpaca_jsonl`
- `chatml_jsonl`
- `preference_jsonl`

Export files are UTF-8, one JSON object per line, `ensure_ascii=false`, and never
include rejected samples.

## API overview

- `GET /v1/datasets`
- `POST /v1/datasets`
- `GET /v1/datasets/{dataset_id}`
- `PATCH /v1/datasets/{dataset_id}`
- `DELETE /v1/datasets/{dataset_id}`
- `POST /v1/datasets/{dataset_id}/samples/from-revision`
- `POST /v1/datasets/{dataset_id}/samples/bulk-from-revisions`
- `GET /v1/datasets/{dataset_id}/samples`
- `GET /v1/datasets/samples/{sample_id}`
- `PATCH /v1/datasets/samples/{sample_id}`
- `DELETE /v1/datasets/samples/{sample_id}`
- `POST /v1/datasets/samples/{sample_id}/approve`
- `POST /v1/datasets/samples/{sample_id}/reject`
- `POST /v1/datasets/{dataset_id}/export`
- `GET /v1/datasets/{dataset_id}/exports`
- `GET /v1/datasets/exports/{export_id}`

## Flutter

Flutter adds Dataset Builder with a dataset list, sample table, sample detail
editor, approve/reject buttons, and SFT JSONL export panel. Revision Review adds
Add to Dataset / Create SFT Sample buttons, but the user must choose a dataset.

## Stage 7 prerequisites

Stage 7 can build on approved samples and export records to add immutable
DatasetVersion, train/val split, manifest, exact hashes, token checks, and
training recipe recommendations.
