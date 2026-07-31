"""Pydantic schemas for Stage 6 Dataset Builder APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreateDatasetRequest(BaseModel):
    name: str
    type: str = "sft"
    description: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class UpdateDatasetRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    project_id: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class CreateSampleFromRevisionRequest(BaseModel):
    revision_id: str
    sample_type: str = "sft"


class BulkCreateSamplesFromRevisionsRequest(BaseModel):
    project_id: str | None = None
    chapter_id: str | None = None
    min_score: int | None = None
    tags: list[str] = Field(default_factory=list)
    accepted_for_dataset: bool = True
    revision_status: str | None = "approved"
    sample_type: str = "sft"
    limit: int = 100


class UpdateSampleRequest(BaseModel):
    instruction: str | None = None
    input: str | None = None
    output: str | None = None
    chosen: str | None = None
    rejected: str | None = None
    quality_score: int | None = None
    status: str | None = None
    review_notes: str | None = None
    metadata: dict[str, Any] | None = None


class RejectSampleRequest(BaseModel):
    reason: str | None = None


class ExportDatasetRequest(BaseModel):
    format: str = "sft_jsonl"
    approved_only: bool = True
    file_name: str | None = None


class DatasetSplitRequest(BaseModel):
    strategy: str = "group_by_chapter"
    val_ratio: float = 0.1
    seed: int = 42


class DatasetDedupeRequest(BaseModel):
    exact_hash: bool = True
    near_duplicate: bool = True
    near_duplicate_threshold: float = 0.92


class FreezeDatasetRequest(BaseModel):
    dataset_id: str | None = None
    name: str
    description: str | None = None
    split: DatasetSplitRequest = Field(default_factory=DatasetSplitRequest)
    dedupe: DatasetDedupeRequest = Field(default_factory=DatasetDedupeRequest)
    export_format: str = "sft_jsonl"
    created_by: str | None = None


class RecommendRecipeRequest(BaseModel):
    base_model_id: str | None = None
    method: str = "qlora"
    hardware: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)


class UpdateRecipeRequest(BaseModel):
    base_model_id: str | None = None
    method: str | None = None
    user_config: dict[str, Any] | None = None
    status: str | None = None
