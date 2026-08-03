# Novel Studio Stage 8: LoRA / QLoRA Fine-tune Center

Stage 8 consumes Stage 7 frozen `dataset_versions` and confirmed
`training_recipes` to create persistent `finetune_runs`. Training is never
performed in the API request thread: the API creates a JobQueue job, the job
runner performs preflight again, acquires the GPU scheduler, then calls the
LoRA or QLoRA trainer.

## Scope

- Create `/v1/finetune/*` APIs.
- Persist `finetune_runs`, `finetune_checkpoints`, `finetune_metrics`, and
  `finetune_logs`.
- Read DatasetVersion manifests and `train.jsonl` / optional `val.jsonl`.
- Require a confirmed TrainingRecipe.
- Track train/eval metrics, best checkpoint, last checkpoint, cancellation,
  resume, and adapter registration.
- Register a completed adapter without auto activation.

## FineTuneRun relation to DatasetVersion and TrainingRecipe

`dataset_versions` are immutable training inputs. `training_recipes` are user
confirmed configuration proposals. `finetune_runs` stores snapshots of both so
the run remains auditable even if the mutable recipe record is later archived.

`config_snapshot_json` intentionally stores model IDs and hyperparameters, not
API keys or local absolute model paths. `dataset_manifest_snapshot_json` stores
the manifest payload with relative artifact paths and hashes.

## Tables

### finetune_runs

The fact source for a training task. Important fields:

- `job_id`: JobQueue job identifier.
- `status`: `created`, `queued`, `preflight`, `running`,
  `saving_checkpoint`, `completed`, `failed`, `cancelled`, or `paused`.
- `current_step`, `total_steps`, `train_loss`, `val_loss`,
  `best_val_loss`: progress and loss summary.
- `best_checkpoint_id`, `last_checkpoint_id`: checkpoint references.
- `adapter_id`: registered adapter id after completion.
- `output_adapter_path`, `metrics_path`, `log_path`: relative artifact paths.

### finetune_checkpoints

Stores `last`, `best`, `periodic`, and `manual` checkpoints. `last` tracks the
most recent safe resume point; `best` is updated only when validation loss
improves.

### finetune_metrics

Stores `train`, `eval`, `checkpoint`, `early_stop`, and `system` events. The
same events are also appended to `data/finetune/runs/{run_id}/metrics.jsonl`.

### finetune_logs

Stores sanitized log messages. API responses do not return Python tracebacks or
secrets.

## Preflight checks

Preflight validates:

- DatasetVersion exists and `status=frozen`.
- Manifest exists, is safe, and its content hash matches the version record.
- `train.jsonl` exists; `val.jsonl` may be absent.
- TrainingRecipe exists, is `confirmed`, and belongs to the requested version.
- Base model exists and is Transformers format.
- Method is `lora` or `qlora`.
- Adapter display name is safe and not already registered.
- Hyperparameters are positive and normalized from Stage 7 recipe keys.
- Output directory is writable.
- Real-trainer dependencies and CUDA/GPU availability are present.

If no validation split exists, early stopping is disabled and a warning is
returned.

## JobQueue and GPU Scheduler integration

`POST /v1/finetune/runs` creates a run and submits a `FINETUNE` JobQueue job
when `start_immediately=true`. `FineTuneJobRunner` runs inside the background
worker, then uses `GpuTaskScheduler.acquire_sync(GpuTaskType.FINETUNE, ...)`
before invoking trainer code.

## Trainer abstraction

`FineTuneTrainer.run(...)` receives the run record, resolved config, dataset
paths, callbacks, and cancellation token. `trainer_lora.py` and
`trainer_qlora.py` wrap the existing local fine-tuning implementation. Tests and
the smoke script can explicitly enable `FakeFineTuneTrainer`; production config
does not silently fake successful training.

## LoRA / QLoRA boundaries

Real LoRA/QLoRA requires local dependencies such as `torch`, `transformers`,
`datasets`, `peft`, and for QLoRA `bitsandbytes`, plus CUDA availability. If
they are missing, preflight returns `FINETUNE_DEPENDENCY_MISSING` or
`FINETUNE_GPU_NOT_AVAILABLE`.

## Checkpoint, early stopping, and resume

The job runner records a last checkpoint whenever the trainer emits a checkpoint
event. If validation loss improves, it records a separate best checkpoint. With
no validation split, the final adapter is exported from last checkpoint behavior
and early stopping is disabled. Resume uses an explicit checkpoint or defaults
to `last_checkpoint_id`.

## Adapter registration

On completion the adapter directory must contain `adapter_config.json` and
`adapter_model.safetensors` or `.bin`. Stage 8 writes
`training_config.json`, `metrics.json`, `dataset_snapshot.json`, and
`novel_finetune_metadata.json`, then registers the adapter through the existing
AdapterRepository. The adapter is not auto activated.

## Flutter Fine-tune Center

Flutter adds:

- Run list.
- Create Run dialog.
- Preflight panel.
- Run detail page.
- Metrics table.
- Logs panel.
- Checkpoint panel.
- Adapter result panel.

The first UI uses a table instead of a full chart component to avoid adding a
large dependency.

## Not included

- Adapter evaluation.
- Base model vs Adapter comparison.
- RAG / Memory.
- Evaluation Center.
- DPO / RLHF.
- Tokenizer training.

## Stage 9 prerequisites

- Completed runs with registered adapters.
- Metrics and checkpoint history available for inspection.
- Adapter evaluation API design that consumes, but does not mutate, Stage 8
  run artifacts.
