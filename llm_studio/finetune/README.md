# llm_studio.finetune

Stage 8 owns the Novel Studio Fine-tune Center lifecycle.

Implemented modules:

- `entities.py`: internal run/checkpoint/metric/log/preflight dataclasses.
- `schemas.py`: API request DTOs.
- `migrations.py`: `finetune_runs`, `finetune_checkpoints`,
  `finetune_metrics`, and `finetune_logs`.
- `repository.py`: SQLite persistence.
- `preflight.py`: frozen DatasetVersion, confirmed recipe, base model,
  dependency, GPU, and output-path checks.
- `trainer.py`: trainer abstraction and explicit fake trainer for tests/smoke.
- `trainer_lora.py` / `trainer_qlora.py`: real trainer adapters around the
  existing local fine-tuning implementation.
- `job_runner.py`: JobQueue handler with GPU Scheduler acquisition.
- `checkpoint_manager.py`: run directory and checkpoint artifact management.
- `metrics.py` / `logs.py`: metrics JSONL and sanitized logs.
- `adapter_registration.py`: adapter artifact registration without auto
  activation.

Boundaries:

- No Adapter evaluation.
- No base model vs Adapter comparison.
- No DPO / RLHF.
- No tokenizer training.
- No RAG / Memory.
- Fake trainer is opt-in for tests and validation; production preflight does
  not fake missing training dependencies.
