"""Pydantic schemas for Context Assembler APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContextBudgetRequest(BaseModel):
    max_tokens: int = 4096
    reserved_output_tokens: int = 1200
    max_context_tokens: int = 2500
    max_chars: int = 12000
    hard_limit: bool = True


class ContextIncludeRequest(BaseModel):
    characters: bool = True
    world_entries: bool = True
    plot_threads: bool = True
    timeline: bool = True
    previous_chapter_summary: bool = True
    chapter_outline: bool = True
    scene_outline: bool = True


class ContextMemoryRequest(BaseModel):
    enabled: bool = False
    query_text: str | None = None
    top_k: int = 12
    max_memory_tokens: int = 1200
    max_chunks: int = 8
    source_types: list[str] = Field(default_factory=list)
    status: str = "active"
    save_retrieval_record: bool = True


class ContextAssemblyRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    template_id: str | None = None
    template_version_id: str | None = None
    mode: str = "chapter_generate"
    target_budget: ContextBudgetRequest = Field(default_factory=ContextBudgetRequest)
    user_variables: dict[str, Any] = Field(default_factory=dict)
    include: ContextIncludeRequest = Field(default_factory=ContextIncludeRequest)
    memory: ContextMemoryRequest = Field(default_factory=ContextMemoryRequest)
    save_record: bool = True


class ContextEstimateRequest(BaseModel):
    text: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
