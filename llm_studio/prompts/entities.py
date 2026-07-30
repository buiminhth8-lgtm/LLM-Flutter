"""Internal Prompt Studio entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PromptTemplate:
    id: str
    name: str
    type: str
    description: str | None
    scope: str
    project_id: str | None
    active_version_id: str | None
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True)
class PromptTemplateVersion:
    id: str
    template_id: str
    version: int
    system_prompt: str | None
    role_prompt: str | None
    instruction_template: str
    negative_prompt: str | None
    output_constraints: str | None
    variables_schema: dict[str, Any]
    default_values: dict[str, Any]
    renderer: str
    change_note: str | None
    created_at: str


@dataclass(frozen=True)
class PromptRenderResult:
    template_id: str
    template_version_id: str
    rendered_prompt: str
    missing_variables: list[str]
    warnings: list[str]
    prompt_hash: str
    render_id: str | None = None
