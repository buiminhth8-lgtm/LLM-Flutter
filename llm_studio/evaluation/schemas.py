"""Pydantic schemas for Stage 11 Evaluation Center APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


def model_dump_compat(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


class EvaluationEvaluatorConfig(BaseModel):
    enabled_evaluators: list[str] = Field(default_factory=list)
    use_local_model_judge: bool = False
    local_model_id: str | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class CreateEvaluationRunRequest(BaseModel):
    name: str
    description: str | None = None
    target_type: str
    target_id: str
    project_id: str | None = None
    chapter_id: str | None = None
    generation_id: str | None = None
    revision_id: str | None = None
    adapter_eval_session_id: str | None = None
    memory_retrieval_id: str | None = None
    run_async: bool = False
    evaluator_config: EvaluationEvaluatorConfig = Field(default_factory=EvaluationEvaluatorConfig)
    context: dict[str, Any] = Field(default_factory=dict)
    created_by: str | None = None


class UpdateFindingRequest(BaseModel):
    status: str


class ManualEvaluationScoreRequest(BaseModel):
    overall_score: int | None = None
    dimensions: dict[str, int] = Field(default_factory=dict)
    notes: str | None = None
    reviewer_id: str | None = None

