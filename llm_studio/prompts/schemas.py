"""Pydantic schemas for Prompt Studio APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PromptTemplateCreateRequest(BaseModel):
    name: str
    type: str
    description: str | None = None
    scope: str = "global"
    project_id: str | None = None
    system_prompt: str | None = None
    role_prompt: str | None = None
    instruction_template: str
    negative_prompt: str | None = None
    output_constraints: str | None = None
    variables_schema: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    renderer: str = "simple_mustache"
    change_note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class PromptTemplateUpdateRequest(BaseModel):
    name: str | None = None
    type: str | None = None
    description: str | None = None
    scope: str | None = None
    project_id: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class PromptTemplateVersionCreateRequest(BaseModel):
    system_prompt: str | None = None
    role_prompt: str | None = None
    instruction_template: str
    negative_prompt: str | None = None
    output_constraints: str | None = None
    variables_schema: dict[str, Any] = Field(default_factory=dict)
    default_values: dict[str, Any] = Field(default_factory=dict)
    renderer: str = "simple_mustache"
    change_note: str | None = None


class PromptRenderRequest(BaseModel):
    template_id: str
    template_version_id: str | None = None
    project_id: str | None = None
    chapter_id: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    save_record: bool = True


class PromptCopyToProjectRequest(BaseModel):
    project_id: str
    name: str | None = None
