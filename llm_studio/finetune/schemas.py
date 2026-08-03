"""Pydantic schemas for Stage 8 Fine-tune Center APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FineTunePreflightRequest(BaseModel):
    dataset_version_id: str
    recipe_id: str
    base_model_id: str
    adapter_name: str


class CreateFineTuneRunRequest(FineTunePreflightRequest):
    start_immediately: bool = True


class ResumeFineTuneRunRequest(BaseModel):
    checkpoint_id: str | None = None


class FineTuneRunFilters(BaseModel):
    status: str | None = None
    dataset_version_id: str | None = None
    base_model_id: str | None = None
    method: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class FineTuneLogFilters(BaseModel):
    level: str | None = None
    since: str | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class FineTuneMetricFilters(BaseModel):
    limit: int = Field(default=500, ge=1, le=2000)
    offset: int = Field(default=0, ge=0)


def model_dump_compat(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)
