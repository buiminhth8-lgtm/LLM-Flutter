"""Pydantic schemas for Novel Studio stage 1 APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    title: str
    slug: str | None = None
    genre: str | None = None
    description: str | None = None
    target_style: str | None = None
    target_audience: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdateRequest(BaseModel):
    title: str | None = None
    genre: str | None = None
    description: str | None = None
    target_style: str | None = None
    target_audience: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class VolumeCreateRequest(BaseModel):
    title: str
    volume_index: int | None = None
    outline: str | None = None
    status: str = "active"


class VolumeUpdateRequest(BaseModel):
    title: str | None = None
    volume_index: int | None = None
    outline: str | None = None
    status: str | None = None


class ChapterCreateRequest(BaseModel):
    title: str
    volume_id: str | None = None
    chapter_index: int | None = None
    outline: str | None = None
    draft_content: str | None = None
    final_content: str | None = None
    summary: str | None = None
    status: str = "outline"


class ChapterUpdateRequest(BaseModel):
    title: str | None = None
    volume_id: str | None = None
    chapter_index: int | None = None
    outline: str | None = None
    draft_content: str | None = None
    final_content: str | None = None
    summary: str | None = None
    status: str | None = None


class SceneCreateRequest(BaseModel):
    title: str
    scene_index: int | None = None
    outline: str | None = None
    content: str | None = None
    pov_character_id: str | None = None
    location: str | None = None
    timeline_note: str | None = None
    status: str = "outline"


class SceneUpdateRequest(BaseModel):
    title: str | None = None
    scene_index: int | None = None
    outline: str | None = None
    content: str | None = None
    pov_character_id: str | None = None
    location: str | None = None
    timeline_note: str | None = None
    status: str | None = None


class CharacterCreateRequest(BaseModel):
    name: str
    aliases: str | None = None
    role: str | None = None
    personality: str | None = None
    background: str | None = None
    goals: str | None = None
    relationships: str | None = None
    speech_style: str | None = None
    appearance: str | None = None
    notes: str | None = None
    status: str = "active"


class CharacterUpdateRequest(BaseModel):
    name: str | None = None
    aliases: str | None = None
    role: str | None = None
    personality: str | None = None
    background: str | None = None
    goals: str | None = None
    relationships: str | None = None
    speech_style: str | None = None
    appearance: str | None = None
    notes: str | None = None
    status: str | None = None


class WorldEntryCreateRequest(BaseModel):
    category: str
    title: str
    content: str
    tags: str | None = None
    priority: int = 0
    status: str = "active"


class WorldEntryUpdateRequest(BaseModel):
    category: str | None = None
    title: str | None = None
    content: str | None = None
    tags: str | None = None
    priority: int | None = None
    status: str | None = None


class PlotThreadCreateRequest(BaseModel):
    title: str
    description: str | None = None
    status: str = "open"
    priority: int = 0
    related_character_ids: str | None = None


class PlotThreadUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    related_character_ids: str | None = None


class TimelineEventCreateRequest(BaseModel):
    title: str
    event_order: int | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    description: str | None = None
    involved_character_ids: str | None = None
    status: str = "active"


class TimelineEventUpdateRequest(BaseModel):
    title: str | None = None
    event_order: int | None = None
    chapter_id: str | None = None
    scene_id: str | None = None
    description: str | None = None
    involved_character_ids: str | None = None
    status: str | None = None
