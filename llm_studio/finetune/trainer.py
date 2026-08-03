"""Trainer abstraction for Stage 8 Fine-tune Center."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .errors import FineTuneTrainingFailedError


class CancellationToken:
    def __init__(self, event: threading.Event | None = None):
        self._event = event or threading.Event()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def throw_if_cancelled(self) -> None:
        if self.is_cancelled:
            from llm_studio.jobs.exceptions import JobCancelledError

            raise JobCancelledError("Fine-tune run was cancelled.")


class FineTuneCallbacks:
    def on_train_metrics(self, step: int, metrics: dict[str, Any]) -> None:
        pass

    def on_eval_metrics(self, step: int, metrics: dict[str, Any]) -> None:
        pass

    def on_checkpoint(self, step: int, checkpoint_path: str, metrics: dict[str, Any]) -> None:
        pass

    def on_log(self, level: str, message: str, event_type: str | None = None) -> None:
        pass


@dataclass(frozen=True)
class FineTuneTrainerResult:
    adapter_path: str
    final_step: int
    train_loss: float | None = None
    val_loss: float | None = None
    finish_reason: str = "completed"


class FineTuneTrainer(Protocol):
    def run(
        self,
        run: dict[str, Any],
        config: dict[str, Any],
        dataset_paths: dict[str, str | None],
        callbacks: FineTuneCallbacks,
        cancellation_token: CancellationToken,
    ) -> FineTuneTrainerResult:
        ...


class FakeFineTuneTrainer:
    """Deterministic fake trainer for tests and the Stage 8 smoke script."""

    def run(
        self,
        run: dict[str, Any],
        config: dict[str, Any],
        dataset_paths: dict[str, str | None],
        callbacks: FineTuneCallbacks,
        cancellation_token: CancellationToken,
    ) -> FineTuneTrainerResult:
        run_dir = Path(str(config["run_dir"]))
        adapter_dir = Path(str(config["adapter_output_dir"]))
        checkpoint_source = run_dir / "_fake_checkpoint_source"
        checkpoint_source.mkdir(parents=True, exist_ok=True)
        total_steps = max(1, int(config.get("total_steps") or 3))
        steps = min(total_steps, int(config.get("fake_steps") or 3))
        callbacks.on_log("info", "Fake fine-tune trainer started.", "start")
        train_loss = None
        val_loss = None
        for step in range(1, steps + 1):
            cancellation_token.throw_if_cancelled()
            train_loss = round(3.0 - step * 0.1, 4)
            epoch = round(step / max(steps, 1), 4)
            callbacks.on_train_metrics(
                step,
                {
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "learning_rate": float(config.get("learning_rate") or 0.0002),
                    "tokens_per_second": 1280,
                    "gpu_memory_gb": 0,
                },
            )
            if dataset_paths.get("val"):
                val_loss = round(3.2 - step * 0.08, 4)
                callbacks.on_eval_metrics(step, {"epoch": epoch, "val_loss": val_loss})
            (checkpoint_source / "checkpoint.json").write_text(
                f'{{"step":{step},"fake":true}}',
                encoding="utf-8",
            )
            callbacks.on_checkpoint(
                step,
                str(checkpoint_source),
                {
                    "epoch": epoch,
                    "train_loss": train_loss,
                    "val_loss": val_loss,
                    "checkpoint_type": "last",
                },
            )
        adapter_dir.mkdir(parents=True, exist_ok=True)
        (adapter_dir / "adapter_config.json").write_text(
            (
                '{"peft_type":"LORA","task_type":"CAUSAL_LM","r":'
                f'{int(config.get("lora_r") or 16)},"lora_alpha":'
                f'{int(config.get("lora_alpha") or 32)},"target_modules":["q_proj","v_proj"],'
                f'"base_model_name_or_path":"{run["base_model_id"]}"}}'
            ),
            encoding="utf-8",
        )
        (adapter_dir / "adapter_model.safetensors").write_bytes(b"fake-adapter")
        callbacks.on_log("info", "Fake fine-tune trainer completed.", "done")
        return FineTuneTrainerResult(
            adapter_path=str(adapter_dir),
            final_step=steps,
            train_loss=train_loss,
            val_loss=val_loss,
        )


class MissingDependencyTrainer:
    def __init__(self, method: str):
        self.method = method

    def run(
        self,
        run: dict[str, Any],
        config: dict[str, Any],
        dataset_paths: dict[str, str | None],
        callbacks: FineTuneCallbacks,
        cancellation_token: CancellationToken,
    ) -> FineTuneTrainerResult:
        raise FineTuneTrainingFailedError(
            f"{self.method} trainer dependencies are not available in this environment."
        )
