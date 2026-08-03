"""Internal entities for context assembly."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ContextBudget:
    max_tokens: int = 4096
    reserved_output_tokens: int = 1200
    max_context_tokens: int = 2500
    max_chars: int = 12000
    hard_limit: bool = True

    @property
    def effective_context_tokens(self) -> int:
        return min(self.max_context_tokens, self.max_tokens - self.reserved_output_tokens)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_tokens": self.max_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "max_context_tokens": self.max_context_tokens,
            "max_chars": self.max_chars,
            "hard_limit": self.hard_limit,
        }


@dataclass(frozen=True)
class ContextWarning:
    code: str
    message: str
    affected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "affected": list(self.affected),
        }


@dataclass(frozen=True)
class ContextAssemblyResult:
    project_id: str
    chapter_id: str | None
    scene_id: str | None
    template_id: str | None
    template_version_id: str | None
    mode: str
    variables: dict[str, Any]
    selected_items: dict[str, list[str]]
    budget: dict[str, Any]
    warnings: list[dict[str, Any]]
    estimated_tokens: int
    estimated_chars: int
    context_hash: str
    context_id: str | None = None
    retrieval_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": self.context_id,
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "scene_id": self.scene_id,
            "template_id": self.template_id,
            "template_version_id": self.template_version_id,
            "mode": self.mode,
            "variables": self.variables,
            "selected_items": self.selected_items,
            "budget": self.budget,
            "warnings": self.warnings,
            "estimated_tokens": self.estimated_tokens,
            "estimated_chars": self.estimated_chars,
            "context_hash": self.context_hash,
            "retrieval_id": self.retrieval_id,
        }
