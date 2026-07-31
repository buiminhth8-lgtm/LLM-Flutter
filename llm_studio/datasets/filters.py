"""Filter helpers for Stage 6 Dataset Builder."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RevisionSampleFilter:
    project_id: str | None = None
    chapter_id: str | None = None
    min_score: int | None = None
    tags: list[str] = field(default_factory=list)
    accepted_for_dataset: bool = True
    revision_status: str | None = "approved"
    sample_type: str = "sft"
    limit: int = 100


@dataclass(frozen=True)
class SampleListFilter:
    status: str | None = None
    sample_type: str | None = None
    revision_id: str | None = None
    limit: int = 50
    offset: int = 0
