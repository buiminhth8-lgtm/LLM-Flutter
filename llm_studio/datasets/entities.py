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
