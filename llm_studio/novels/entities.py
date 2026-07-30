"""Internal Novel Studio entity definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NovelProject:
    id: str
    title: str
    slug: str
    genre: str | None
    description: str | None
    target_style: str | None
    target_audience: str | None
    status: str
    metadata_json: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelVolume:
    id: str
    project_id: str
    title: str
    volume_index: int
    outline: str | None
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelChapter:
    id: str
    project_id: str
    volume_id: str | None
    title: str
    chapter_index: int
    outline: str | None
    draft_content: str | None
    final_content: str | None
    summary: str | None
    word_count: int
    status: str
    version: int
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelScene:
    id: str
    project_id: str
    chapter_id: str
    title: str
    scene_index: int
    outline: str | None
    content: str | None
    pov_character_id: str | None
    location: str | None
    timeline_note: str | None
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelCharacter:
    id: str
    project_id: str
    name: str
    aliases: str | None
    role: str | None
    personality: str | None
    background: str | None
    goals: str | None
    relationships: str | None
    speech_style: str | None
    appearance: str | None
    notes: str | None
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelWorldEntry:
    id: str
    project_id: str
    category: str
    title: str
    content: str
    tags: str | None
    priority: int
    status: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelPlotThread:
    id: str
    project_id: str
    title: str
    description: str | None
    status: str
    priority: int
    related_character_ids: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class NovelTimelineEvent:
    id: str
    project_id: str
    title: str
    event_order: int
    chapter_id: str | None
    scene_id: str | None
    description: str | None
    involved_character_ids: str | None
    created_at: str
    updated_at: str
