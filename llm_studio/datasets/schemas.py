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
