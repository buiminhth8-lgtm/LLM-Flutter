"""Pydantic schemas for Novel Studio Stage 10 Memory APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MemoryDocumentCreateRequest(BaseModel):
    project_id: str
    source_type: str = "manual_note"
    source_id: str | None = None
    title: str
    content: str
    summary: str | None = None
    tags: list[str] = Field(default_factory=list)
    priority: int = 0
    status: str = "active"
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryDocumentUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    tags: list[str] | None = None
    priority: int | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class MemoryBuildIncludeRequest(BaseModel):
    chapters: bool = True
    scenes: bool = True
    characters: bool = True
    world_entries: bool = True
    plot_threads: bool = True
    timeline_events: bool = True
    revisions: bool = True
    generations: bool = False
    adapter_eval_results: bool = False


class MemoryBuildRequest(BaseModel):
    include: MemoryBuildIncludeRequest = Field(default_factory=MemoryBuildIncludeRequest)
    rebuild_index: bool = True


class MemoryBudgetRequest(BaseModel):
    max_memory_tokens: int = 1200
    max_chunks: int = 8


class MemoryFiltersRequest(BaseModel):
    source_types: list[str] = Field(default_factory=list)
    status: str = "active"


class MemoryRetrieveRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    query_text: str
    mode: str = "retrieve"
    top_k: int = 12
    budget: MemoryBudgetRequest = Field(default_factory=MemoryBudgetRequest)
    filters: MemoryFiltersRequest = Field(default_factory=MemoryFiltersRequest)
    save_retrieval_record: bool = True


class ChapterSummaryCreateRequest(BaseModel):
    summary_type: str = "short"
    summary_text: str
    set_active: bool = True


class ChapterSummaryGenerateRequest(BaseModel):
    summary_type: str = "short"
    model_id: str
    source: str = "draft_content"
    max_chars: int = 500
    set_active: bool = False
    prompt_template_id: str | None = None


class ChapterSummaryActivateRequest(BaseModel):
    sync_to_chapter: bool = True

