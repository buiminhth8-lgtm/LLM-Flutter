"""Internal entities for Novel Studio revisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RevisionRecord:
    revision_id: str
    project_id: str
    original_text: str
    edited_text: str
    diff: dict[str, Any]
    edit_tags: list[str]
    status: str
    accepted_for_dataset: bool
    source: str
    original_hash: str
    edited_hash: str
    created_at: str
    updated_at: str
    generation_id: str | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    user_score: int | None = None
    quality_notes: str | None = None
    reviewer_id: str | None = None
    warnings: list[dict[str, Any]] = field(default_factory=list)
