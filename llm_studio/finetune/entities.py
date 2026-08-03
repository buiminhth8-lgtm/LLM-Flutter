"""Internal entities for Novel Studio Stage 8 Fine-tune Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class FineTuneRun:
    run_id: str
    dataset_version_id: str
    recipe_id: str
    base_model_id: str
    method: str
    adapter_name: str
    status: str
    config_snapshot: dict[str, Any]
    dataset_manifest_snapshot: dict[str, Any]
    current_step: int
    total_steps: int
    created_at: str
    updated_at: str
    job_id: str | None = None
    adapter_id: str | None = None
    current_epoch: float | None = None
    train_loss: float | None = None
    val_loss: float | None = None
    best_val_loss: float | None = None
    best_step: int | None = None
    best_checkpoint_id: str | None = None
    last_checkpoint_id: str | None = None
    output_adapter_path: str | None = None
    metrics_path: str | None = None
    log_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    cancel_requested: bool = False
    resume_from_checkpoint_id: str | None = None
    started_at: str | None = None
    finished_at: str | None = None


@dataclass(frozen=True)
class FineTuneCheckpoint:
    checkpoint_id: str
    run_id: str
    checkpoint_type: str
    step: int
    checkpoint_path: str
    created_at: str
    epoch: float | None = None
    train_loss: float | None = None
    val_loss: float | None = None
    checkpoint_hash: str | None = None
    size_bytes: int | None = None
    is_best: bool = False
    is_last: bool = False


@dataclass(frozen=True)
class FineTuneMetric:
    metric_id: str
    run_id: str
    step: int
    metric_type: str
    metrics: dict[str, Any]
    created_at: str
    epoch: float | None = None


@dataclass(frozen=True)
class FineTuneLog:
    log_id: str
    run_id: str
    level: str
    message: str
    created_at: str
    event_type: str | None = None
    step: int | None = None


@dataclass(frozen=True)
class FineTunePreflightResult:
    ok: bool
    errors: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    resolved_config: dict[str, Any] = field(default_factory=dict)
