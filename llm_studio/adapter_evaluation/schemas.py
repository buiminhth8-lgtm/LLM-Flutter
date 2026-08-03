"""Pydantic request schemas for Novel Studio Stage 9 Adapter Evaluation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


def model_dump_compat(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


class AdapterEvalCreateSessionRequest(BaseModel):
    name: str
    description: str | None = None
    project_id: str | None = None
    finetune_run_id: str | None = None
    dataset_version_id: str | None = None
    base_model_id: str
    adapter_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class AdapterEvalUpdateSessionRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class AdapterEvalCreateCaseRequest(BaseModel):
    title: str
    project_id: str | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    template_id: str
    template_version_id: str | None = None
    context_id: str | None = None
    mode: str
    user_variables: dict[str, Any] = Field(default_factory=dict)
    generation_params: dict[str, Any] = Field(default_factory=dict)
    target_length: dict[str, Any] = Field(default_factory=dict)


class AdapterEvalRunSessionRequest(BaseModel):
    case_ids: list[str] = Field(default_factory=list)
    rerun_completed: bool = False


class AdapterEvalScoreRequest(BaseModel):
    winner: str | None = None
    base_score: int | None = None
    adapter_score: int | None = None
    dimensions: dict[str, dict[str, int | None]] = Field(default_factory=dict)
    notes: str | None = None
    reviewer_id: str | None = None


class AdapterEvalCreateRevisionRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    source_original: str = "base"
    edit_tags: list[str] = Field(default_factory=list)
    user_score: int | None = None
    quality_notes: str | None = None
    reviewer_id: str | None = None
