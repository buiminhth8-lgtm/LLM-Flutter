"""Pydantic request schemas for Novel Studio writing APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TargetLengthRequest(BaseModel):
    unit: str = "chars"
    min: int = 1200
    max: int = 1800
    strategy: str = "soft"


class WritingGenerationParamsRequest(BaseModel):
    temperature: float = 0.8
    top_p: float = 0.9
    max_tokens: int | None = None
    repetition_penalty: float = 1.1
    stream: bool = False
    stop: list[str] = Field(default_factory=list)


class WritingGenerationRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    template_id: str | None = None
    template_version_id: str | None = None
    context_id: str | None = None
    model_id: str
    adapter_id: str | None = None
    mode: str = "chapter_generate"
    target_length: TargetLengthRequest = Field(default_factory=TargetLengthRequest)
    user_variables: dict[str, Any] = Field(default_factory=dict)
    generation_params: WritingGenerationParamsRequest = Field(
        default_factory=WritingGenerationParamsRequest
    )
    save_to_chapter: bool = False


class SaveGenerationRequest(BaseModel):
    target: str = "draft_content"
    append: bool = False
