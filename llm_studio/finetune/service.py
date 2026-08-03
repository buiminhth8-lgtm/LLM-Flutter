"""FineTuneService orchestration for Novel Studio Stage 8."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from llm_studio.jobs import JobType
from llm_studio.jobs.exceptions import JobCancelNotAllowedError, JobQueueClosedError
from llm_studio.runtime.gpu_scheduler import GpuTaskScheduler
from llm_studio.security.redaction import redact_sensitive_text

from .adapter_registration import FineTuneAdapterRegistration
from .checkpoint_manager import FineTuneCheckpointManager
from .errors import (
    FineTuneCancelNotSupportedError,
    FineTuneCheckpointNotFoundError,
    FineTuneJobCreateFailedError,
    FineTuneResumeFailedError,
)
from .job_runner import FineTuneJobRunner
from .preflight import FineTunePreflight
from .repository import FineTuneRepository
from .schemas import model_dump_compat
from .trainer import FakeFineTuneTrainer, FineTuneTrainer, MissingDependencyTrainer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FineTuneService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        output_root: str | Path,
        dataset_service: Any,
        model_repository: Any,
        adapter_repository: Any,
        job_queue: Any,
        gpu_scheduler: GpuTaskScheduler | None = None,
        default_config: dict[str, Any] | None = None,
        use_fake_trainer: bool = False,
        trainer_factory: Any | None = None,
        dependency_checker: Any | None = None,
    ):
        self.db_path = Path(db_path)
        self.output_root = Path(output_root)
        self.records = FineTuneRepository(self.db_path)
        self.dataset_service = dataset_service
        self.model_repository = model_repository
        self.adapter_repository = adapter_repository
        self.job_queue = job_queue
        self.gpu_scheduler = gpu_scheduler or GpuTaskScheduler(enabled=False)
        self.default_config = default_config or {}
        self.use_fake_trainer = use_fake_trainer
        self.trainer_factory = trainer_factory
        self.checkpoints = FineTuneCheckpointManager(self.output_root)
        self.preflight_checker = FineTunePreflight(
            dataset_service=dataset_service,
            model_repository=model_repository,
            adapter_repository=adapter_repository,
            output_root=self.output_root,
            default_config=self.default_config,
            use_fake_trainer=use_fake_trainer,
            dependency_checker=dependency_checker or None,
        )
        if dependency_checker is None:
            from .preflight import default_dependency_checker

            self.preflight_checker.dependency_checker = default_dependency_checker
        self.adapter_registration = FineTuneAdapterRegistration(
            adapter_repository,
            checkpoint_manager=self.checkpoints,
        )
        self.job_runner = FineTuneJobRunner(self)

    @classmethod
    def from_config(
        cls,
        config: Any,
        *,
        dataset_service: Any,
        model_repository: Any,
        adapter_repository: Any,
        job_queue: Any,
        gpu_scheduler: GpuTaskScheduler | None = None,
    ) -> FineTuneService:
        cfg = config.get("finetune", {}) if config is not None else {}
        datasets_cfg = config.get("datasets", {}) if config is not None else {}
        fallback_db = datasets_cfg.get(
            "db_path",
            config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite")
            if config is not None
            else "./data/novels/novels.sqlite",
        )
        raw_output = cfg.get("output_dir", "./data/finetune")
        output_root = Path(raw_output)
        if config is not None and not output_root.is_absolute():
            output_root = config.config_path.parent / output_root
        return cls(
            Path(cfg.get("db_path", fallback_db)),
            output_root=output_root,
            dataset_service=dataset_service,
            model_repository=model_repository,
            adapter_repository=adapter_repository,
            job_queue=job_queue,
            gpu_scheduler=gpu_scheduler,
            default_config=dict(cfg),
            use_fake_trainer=bool(cfg.get("use_fake_trainer", False)),
        )

    def preflight(self, request: Any, *, raise_on_error: bool = False) -> dict[str, Any]:
        result = self.preflight_checker.run(request, raise_on_error=raise_on_error)
        return {
            key: value
            for key, value in result.items()
            if not key.startswith("_") and key not in {"dataset_version", "training_recipe"}
        } | {
            "_dataset_paths": result.get("_dataset_paths"),
            "_model_path": result.get("_model_path"),
            "dataset_version": result.get("dataset_version"),
            "training_recipe": result.get("training_recipe"),
        }

    def preflight_public(self, request: Any) -> dict[str, Any]:
        result = self.preflight_checker.run(request, raise_on_error=False)
        return {
            "ok": result["ok"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "resolved_config": result["resolved_config"],
        }

    def create_run(self, request: Any) -> dict[str, Any]:
        data = model_dump_compat(request)
        preflight = self.preflight(data, raise_on_error=True)
        run_id = str(uuid.uuid4())
        layout = self.checkpoints.ensure_run_layout(run_id)
        public_config = {
            **preflight["resolved_config"],
            "dataset_version_id": data["dataset_version_id"],
            "recipe_id": data["recipe_id"],
            "base_model_id": data["base_model_id"],
            "adapter_name": data["adapter_name"],
        }
        manifest = preflight["dataset_manifest"]
        total_steps = self._estimate_total_steps(
            preflight["dataset_version"],
            public_config,
        )
        metrics_path = self.checkpoints.relative_path(layout["run_dir"] / "metrics.jsonl")
        log_path = self.checkpoints.relative_path(layout["run_dir"] / "train.log")
        (layout["run_dir"] / "config_snapshot.json").write_text(
            json.dumps(public_config, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (layout["run_dir"] / "dataset_manifest_snapshot.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        run = self.records.create_run(
            {
                "id": run_id,
                "dataset_version_id": data["dataset_version_id"],
                "recipe_id": data["recipe_id"],
                "base_model_id": data["base_model_id"],
                "method": preflight["training_recipe"]["method"],
                "adapter_name": data["adapter_name"],
                "status": "created",
                "config_snapshot": public_config,
                "dataset_manifest_snapshot": manifest,
                "total_steps": total_steps,
                "metrics_path": metrics_path,
                "log_path": log_path,
            }
        )
        if bool(data.get("start_immediately", True)):
            return self.start_run(run["run_id"])
        return self.get_run(run["run_id"])

    def start_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        if run["status"] not in {"created", "paused", "failed", "cancelled"}:
            return self.get_run(run_id)
        try:
            job = self.job_queue.submit(
                JobType.FINETUNE.value,
                {"run_id": run_id, "dataset_version_id": run["dataset_version_id"]},
                self.job_runner.handle,
            )
        except (JobQueueClosedError, Exception) as exc:
            if isinstance(exc, JobQueueClosedError):
                raise FineTuneJobCreateFailedError("JobQueue is closed.") from exc
            raise FineTuneJobCreateFailedError("Failed to create fine-tune job.") from exc
        self.records.update_run(
            run_id,
            {
                "job_id": job.id,
                "status": "queued",
                "cancel_requested": 0,
                "error_code": None,
                "error_message": None,
            },
        )
        return self.get_run(run_id)

    def cancel_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        self.records.update_run(run_id, {"cancel_requested": 1})
        job_id = run.get("job_id")
        if job_id:
            try:
                self.job_queue.cancel(job_id)
            except JobCancelNotAllowedError as exc:
                if run["status"] not in {"completed", "failed", "cancelled"}:
                    raise FineTuneCancelNotSupportedError(
                        "Fine-tune run cannot be cancelled now."
                    ) from exc
        return self.get_run(run_id)

    def resume_run(self, run_id: str, checkpoint_id: str | None = None) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        checkpoint = None
        if checkpoint_id:
            checkpoint = self.records.get_checkpoint(checkpoint_id)
            if checkpoint["run_id"] != run_id:
                raise FineTuneCheckpointNotFoundError(checkpoint_id)
        elif run.get("last_checkpoint_id"):
            checkpoint = self.records.get_checkpoint(run["last_checkpoint_id"])
        else:
            raise FineTuneResumeFailedError("No checkpoint is available for resume.")
        self.records.update_run(
            run_id,
            {
                "status": "created",
                "cancel_requested": 0,
                "resume_from_checkpoint_id": checkpoint["checkpoint_id"],
            },
        )
        return self.start_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self.records.get_run(run_id)
        return {
            **run,
            "metrics": self.records.list_metrics(run_id, limit=100),
            "logs": self.records.list_logs(run_id, limit=100),
            "checkpoints": self.records.list_checkpoints(run_id),
        }

    def list_runs(
        self,
        *,
        status: str | None = None,
        dataset_version_id: str | None = None,
        base_model_id: str | None = None,
        method: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_runs(
            status=status,
            dataset_version_id=dataset_version_id,
            base_model_id=base_model_id,
            method=method,
            limit=limit,
            offset=offset,
        )

    def get_metrics(self, run_id: str, *, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        return self.records.list_metrics(run_id, limit=limit, offset=offset)

    def get_logs(
        self,
        run_id: str,
        *,
        level: str | None = None,
        since: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return self.records.list_logs(run_id, level=level, since=since, limit=limit, offset=offset)

    def get_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        return self.records.list_checkpoints(run_id)

    def trainer_for(self, method: str) -> FineTuneTrainer:
        if self.trainer_factory is not None:
            return self.trainer_factory(method)
        if self.use_fake_trainer:
            return FakeFineTuneTrainer()
        if method == "lora":
            from .trainer_lora import LoraFineTuneTrainer

            return LoraFineTuneTrainer()
        if method == "qlora":
            from .trainer_qlora import QLoraFineTuneTrainer

            return QLoraFineTuneTrainer()
        return MissingDependencyTrainer(method)

    def trainer_config(
        self,
        run_id: str,
        run: dict[str, Any],
        preflight: dict[str, Any],
    ) -> dict[str, Any]:
        layout = self.checkpoints.ensure_run_layout(run_id)
        config = {
            **run.get("config_snapshot", {}),
            "run_dir": str(layout["run_dir"]),
            "adapter_output_dir": str(layout["adapter"]),
            "model_path": preflight["_model_path"],
            "train_path": preflight["_dataset_paths"]["train"],
            "val_path": preflight["_dataset_paths"].get("val"),
            "total_steps": run.get("total_steps") or 1,
        }
        if run.get("resume_from_checkpoint_id"):
            checkpoint = self.records.get_checkpoint(run["resume_from_checkpoint_id"])
            root = self.output_root.resolve().parent
            config["resume_from_checkpoint_path"] = str((root / checkpoint["checkpoint_path"]).resolve())
        return config

    @staticmethod
    def _estimate_total_steps(version: dict[str, Any], config: dict[str, Any]) -> int:
        train_count = max(1, int(version.get("train_sample_count") or 1))
        epochs = int(config.get("num_epochs") or config.get("epochs") or 1)
        batch = max(1, int(config.get("batch_size") or config.get("per_device_train_batch_size") or 1))
        grad = max(1, int(config.get("gradient_accumulation_steps") or 1))
        return max(1, (train_count * max(1, epochs) + batch * grad - 1) // (batch * grad))


def public_error_message(exc: Exception) -> str:
    return redact_sensitive_text(str(exc)) or "Fine-tune failed."
