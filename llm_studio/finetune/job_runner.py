"""JobQueue entry point for fine-tune runs."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from llm_studio.jobs.exceptions import JobCancelledError
from llm_studio.runtime.gpu_scheduler import GpuTaskRequest, GpuTaskType

from .logs import FineTuneLogWriter, sanitize_finetune_log
from .metrics import FineTuneMetricsWriter
from .trainer import CancellationToken, FineTuneCallbacks


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FineTuneJobRunner:
    def __init__(self, service: Any):
        self.service = service

    def handle(self, job: Any, update: Callable[[float | None, str | None], None], cancel_event: Any) -> None:
        run_id = str(job.payload["run_id"])
        run = self.service.records.get_run(run_id)
        run_dir = self.service.checkpoints.ensure_run_layout(run_id)["run_dir"]
        metrics_writer = FineTuneMetricsWriter(run_dir)
        log_writer = FineTuneLogWriter(run_dir)

        def log(level: str, message: str, event_type: str | None = None, step: int | None = None) -> None:
            clean = sanitize_finetune_log(message)
            log_writer.append(level, clean, event_type=event_type, step=step)
            self.service.records.create_log(
                {
                    "run_id": run_id,
                    "level": level,
                    "message": clean,
                    "event_type": event_type,
                    "step": step,
                }
            )

        try:
            update(0.02, "Fine-tune preflight.")
            self.service.records.update_run(
                run_id,
                {
                    "status": "preflight",
                    "error_code": None,
                    "error_message": None,
                    "cancel_requested": 0,
                },
            )
            preflight = self.service.preflight(
                {
                    "dataset_version_id": run["dataset_version_id"],
                    "recipe_id": run["recipe_id"],
                    "base_model_id": run["base_model_id"],
                    "adapter_name": run["adapter_name"],
                },
                raise_on_error=True,
            )
            config = self.service.trainer_config(run_id, run, preflight)
            token = CancellationToken(cancel_event)
            with self.service.gpu_scheduler.acquire_sync(
                GpuTaskRequest(GpuTaskType.FINETUNE, "novel-finetune", job.id)
            ):
                update(0.08, "Fine-tune running.")
                self.service.records.update_run(
                    run_id,
                    {
                        "status": "running",
                        "started_at": run.get("started_at") or _now(),
                    },
                )
                log("info", "Fine-tune job started.", "start")
                callbacks = _RepositoryCallbacks(
                    service=self.service,
                    run_id=run_id,
                    update=update,
                    metrics_writer=metrics_writer,
                    log_writer=log_writer,
                )
                trainer = self.service.trainer_for(run["method"])
                result = trainer.run(
                    run,
                    config,
                    preflight["_dataset_paths"],
                    callbacks,
                    token,
                )
                token.throw_if_cancelled()
                run = self.service.records.get_run(run_id)
                if run.get("last_checkpoint_id") is None:
                    callbacks.on_checkpoint(
                        result.final_step,
                        result.adapter_path,
                        {
                            "checkpoint_type": "last",
                            "train_loss": result.train_loss,
                            "val_loss": result.val_loss,
                        },
                    )
                run = self.service.records.get_run(run_id)
                update(0.92, "Registering adapter.")
                registered = self.service.adapter_registration.register(
                    run=run,
                    adapter_path=result.adapter_path,
                    metrics={
                        "train_loss": result.train_loss,
                        "val_loss": result.val_loss,
                        "best_val_loss": run.get("best_val_loss"),
                        "final_step": result.final_step,
                    },
                )
                self.service.records.update_run(
                    run_id,
                    {
                        "status": "completed",
                        "adapter_id": registered["adapter_id"],
                        "output_adapter_path": registered["output_adapter_path"],
                        "current_step": result.final_step,
                        "train_loss": result.train_loss,
                        "val_loss": result.val_loss,
                        "finished_at": _now(),
                    },
                )
                log("info", "Adapter registered without auto activation.", "adapter_registered")
                update(1.0, "Fine-tune completed.")
        except JobCancelledError:
            checkpoint = self.service.records.get_run(run_id).get("last_checkpoint_id")
            self.service.records.update_run(
                run_id,
                {
                    "status": "cancelled",
                    "cancel_requested": 1,
                    "last_checkpoint_id": checkpoint,
                    "finished_at": _now(),
                },
            )
            log("warning", "Fine-tune run cancelled.", "cancelled")
            raise
        except Exception as exc:
            code = getattr(exc, "code", getattr(exc, "error_code", "FINETUNE_TRAINING_FAILED"))
            message = sanitize_finetune_log(str(exc))
            self.service.records.update_run(
                run_id,
                {
                    "status": "failed",
                    "error_code": code,
                    "error_message": message,
                    "finished_at": _now(),
                },
            )
            log("error", message, "failed")
            raise


class _RepositoryCallbacks(FineTuneCallbacks):
    def __init__(
        self,
        *,
        service: Any,
        run_id: str,
        update: Callable[[float | None, str | None], None],
        metrics_writer: FineTuneMetricsWriter,
        log_writer: FineTuneLogWriter,
    ):
        self.service = service
        self.run_id = run_id
        self.update = update
        self.metrics_writer = metrics_writer
        self.log_writer = log_writer

    def on_train_metrics(self, step: int, metrics: dict[str, Any]) -> None:
        epoch = metrics.get("epoch")
        self.metrics_writer.append("train", step=step, epoch=epoch, metrics=metrics)
        self.service.records.create_metric(
            {
                "run_id": self.run_id,
                "step": step,
                "epoch": epoch,
                "metric_type": "train",
                "metrics": metrics,
            }
        )
        total = max(1, int(self.service.records.get_run(self.run_id).get("total_steps") or 1))
        self.service.records.update_run(
            self.run_id,
            {
                "current_step": step,
                "current_epoch": epoch,
                "train_loss": metrics.get("train_loss"),
            },
        )
        self.update(min(0.9, 0.1 + step / total * 0.75), f"Training step {step}/{total}")

    def on_eval_metrics(self, step: int, metrics: dict[str, Any]) -> None:
        epoch = metrics.get("epoch")
        self.metrics_writer.append("eval", step=step, epoch=epoch, metrics=metrics)
        self.service.records.create_metric(
            {
                "run_id": self.run_id,
                "step": step,
                "epoch": epoch,
                "metric_type": "eval",
                "metrics": metrics,
            }
        )
        self.service.records.update_run(
            self.run_id,
            {
                "current_step": step,
                "current_epoch": epoch,
                "val_loss": metrics.get("val_loss"),
            },
        )

    def on_checkpoint(self, step: int, checkpoint_path: str, metrics: dict[str, Any]) -> None:
        checkpoint_type = str(metrics.get("checkpoint_type") or "last")
        run = self.service.records.get_run(self.run_id)
        payload = self.service.checkpoints.record_checkpoint(
            self.run_id,
            checkpoint_type=checkpoint_type,
            step=step,
            source_path=checkpoint_path,
            metrics=metrics,
        )
        checkpoint = self.service.records.create_checkpoint(
            {
                **payload,
                "run_id": self.run_id,
                "is_last": checkpoint_type == "last",
                "is_best": False,
            }
        )
        changes: dict[str, Any] = {
            "status": "saving_checkpoint" if run.get("status") == "running" else run.get("status"),
            "last_checkpoint_id": checkpoint["checkpoint_id"] if checkpoint_type == "last" else run.get("last_checkpoint_id"),
            "current_step": step,
        }
        val_loss = metrics.get("val_loss")
        best_val_loss = run.get("best_val_loss")
        if val_loss is not None and (best_val_loss is None or float(val_loss) < float(best_val_loss)):
            best_payload = self.service.checkpoints.record_checkpoint(
                self.run_id,
                checkpoint_type="best",
                step=step,
                source_path=checkpoint_path,
                metrics=metrics,
            )
            best = self.service.records.create_checkpoint(
                {
                    **best_payload,
                    "run_id": self.run_id,
                    "is_best": True,
                    "is_last": False,
                }
            )
            changes.update(
                {
                    "best_checkpoint_id": best["checkpoint_id"],
                    "best_val_loss": float(val_loss),
                    "best_step": step,
                }
            )
        self.service.records.update_run(self.run_id, changes)
        self.metrics_writer.append(
            "checkpoint",
            step=step,
            epoch=metrics.get("epoch"),
            metrics={"checkpoint_type": checkpoint_type, "path": payload["checkpoint_path"]},
        )
        self.service.records.create_metric(
            {
                "run_id": self.run_id,
                "step": step,
                "epoch": metrics.get("epoch"),
                "metric_type": "checkpoint",
                "metrics": {"checkpoint_type": checkpoint_type, "path": payload["checkpoint_path"]},
            }
        )
        if run.get("status") == "running":
            self.service.records.update_run(self.run_id, {"status": "running"})

    def on_log(self, level: str, message: str, event_type: str | None = None) -> None:
        clean = sanitize_finetune_log(message)
        self.log_writer.append(level, clean, event_type=event_type)
        self.service.records.create_log(
            {
                "run_id": self.run_id,
                "level": level,
                "message": clean,
                "event_type": event_type,
            }
        )
