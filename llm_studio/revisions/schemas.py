"""Pydantic request schemas for Novel Studio revision APIs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RevisionCreateFromGenerationRequest(BaseModel):
    generation_id: str
    edited_text: str | None = None
    edit_tags: list[str] = Field(default_factory=list)
    user_score: int | None = None
    quality_notes: str | None = None
    accepted_for_dataset: bool = False
    reviewer_id: str | None = None


class RevisionCreateFromChapterDraftRequest(BaseModel):
    project_id: str
    chapter_id: str
    scene_id: str | None = None
    original_text: str | None = None
    edited_text: str
    edit_tags: list[str] = Field(default_factory=list)
    user_score: int | None = None
    quality_notes: str | None = None
    accepted_for_dataset: bool = False
    reviewer_id: str | None = None


class RevisionManualCreateRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    scene_id: str | None = None
    original_text: str
    edited_text: str
    edit_tags: list[str] = Field(default_factory=list)
    user_score: int | None = None
    quality_notes: str | None = None
    accepted_for_dataset: bool = False
    reviewer_id: str | None = None


class RevisionUpdateRequest(BaseModel):
    edited_text: str | None = None
    edit_tags: list[str] | None = None
    user_score: int | None = None
    quality_notes: str | None = None
    status: str | None = None
    accepted_for_dataset: bool | None = None
    reviewer_id: str | None = None
    expected_updated_at: str | None = None


class RevisionRejectRequest(BaseModel):
    reason: str | None = None


class RevisionDatasetCandidateRequest(BaseModel):
    accepted: bool = True


class RevisionAutosaveRequest(BaseModel):
    revision_id: str | None = None
    project_id: str
    chapter_id: str | None = None
    generation_id: str | None = None
    draft_text: str
    base_text_hash: str | None = None
    client_revision: int = 1
