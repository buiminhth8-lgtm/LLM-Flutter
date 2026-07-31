"""Internal entities for Novel Studio Dataset Builder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TrainingDataset:
    dataset_id: str
    name: str
    type: str
    status: str
    sample_count: int
    approved_sample_count: int
    rejected_sample_count: int
    created_at: str
    updated_at: str
    description: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_by: str | None = None


@dataclass(frozen=True)
class TrainingSampleDraft:
    sample_type: str
    instruction: str
    input: str
    output: str
    source_hash: str
    content_hash: str
    project_id: str | None = None
    chapter_id: str | None = None
    revision_id: str | None = None
    generation_id: str | None = None
    chosen: str | None = None
    rejected: str | None = None
    quality_score: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TrainingSample:
    sample_id: str
    dataset_id: str
    sample_type: str
    instruction: str
    input: str
    output: str
    source_hash: str
    content_hash: str
    status: str
    created_at: str
    updated_at: str
    project_id: str | None = None
    chapter_id: str | None = None
    revision_id: str | None = None
    generation_id: str | None = None
    chosen: str | None = None
    rejected: str | None = None
    quality_score: int | None = None
    review_notes: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DatasetExportRecord:
    export_id: str
    dataset_id: str
    export_format: str
    export_path: str
    sample_count: int
    approved_only: bool
    status: str
    created_at: str
    export_hash: str | None = None


@dataclass(frozen=True)
class DatasetVersion:
    dataset_version_id: str
    dataset_id: str
    version: int
    name: str
    status: str
    source_sample_count: int
    train_sample_count: int
    val_sample_count: int
    rejected_duplicate_count: int
    warning_count: int
    train_char_count: int
    val_char_count: int
    train_token_estimate: int
    val_token_estimate: int
    content_hash: str
    manifest_path: str
    train_path: str
    created_at: str
    description: str | None = None
    val_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DatasetVersionSample:
    dataset_version_sample_id: str
    dataset_version_id: str
    sample_id: str
    split: str
    sample_order: int
    content_hash: str
    source_hash: str | None
    char_count: int
    token_estimate: int
    created_at: str
    duplicate_group_id: str | None = None
    warnings: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class TrainingRecipe:
    recipe_id: str
    dataset_version_id: str
    method: str
    recommended_config: dict[str, Any]
    user_config: dict[str, Any]
    status: str
    created_at: str
    updated_at: str
    base_model_id: str | None = None
    recommendation_reason: str | None = None
    estimated_vram_gb: float | None = None
    estimated_train_time_minutes: int | None = None
    warnings: list[dict[str, Any]] = field(default_factory=list)
