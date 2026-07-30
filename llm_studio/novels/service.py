"""Business service for Novel Studio foundation CRUD."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import NovelValidationError
from .migrations import initialize_novel_database
from .repository import (
    NovelChapterRepository,
    NovelCharacterRepository,
    NovelPlotThreadRepository,
    NovelProjectRepository,
    NovelSceneRepository,
    NovelTimelineRepository,
    NovelVolumeRepository,
    NovelWorldEntryRepository,
    word_count_for,
)


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_unset=True)
    if hasattr(value, "dict"):
        return value.dict(exclude_unset=True)
    return dict(value)


def _require_text(value: str | None, field: str) -> str:
    text = (value or "").strip()
    if not text:
        raise NovelValidationError(f"{field} is required.")
    return text


def _safe_slug(value: str) -> str:
    text = value.strip().lower()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", text)
    slug = re.sub(r"-+", "-", slug).strip("-_")
    return slug or "novel"


class NovelService:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        initialize_novel_database(self.db_path)
        self.projects = NovelProjectRepository(self.db_path)
        self.volumes = NovelVolumeRepository(self.db_path)
        self.chapters = NovelChapterRepository(self.db_path)
        self.scenes = NovelSceneRepository(self.db_path)
        self.characters = NovelCharacterRepository(self.db_path)
        self.world_entries = NovelWorldEntryRepository(self.db_path)
        self.plot_threads = NovelPlotThreadRepository(self.db_path)
        self.timeline = NovelTimelineRepository(self.db_path)

    @classmethod
    def from_config(cls, config: Any) -> NovelService:
        cfg = config.get("novels", {}) if config is not None else {}
        db_path = cfg.get("db_path", "./data/novels/novels.sqlite")
        return cls(Path(db_path))

    def list_projects(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return self.projects.list(limit=limit, offset=offset)

    def create_project(self, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        title = _require_text(data.get("title"), "title")
        slug = _safe_slug(data.get("slug") or title)
        payload = {**data, "title": title, "slug": slug}
        return self.projects.create(payload)

    def get_project(self, project_id: str) -> dict[str, Any]:
        return self.projects.get(project_id)

    def update_project(self, project_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        if "metadata" in data:
            data["metadata_json"] = json.dumps(data.pop("metadata") or {}, ensure_ascii=False)
        return self.projects.update(project_id, data)

    def delete_project(self, project_id: str) -> dict[str, Any]:
        return self.projects.soft_delete(project_id)

    def list_volumes(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.volumes.list(project_id=project_id, limit=limit, offset=offset)

    def create_volume(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = project_id
        if data.get("volume_index") is None:
            data["volume_index"] = self.volumes.next_index("volume_index", project_id=project_id)
        return self.volumes.create(data)

    def update_volume(self, volume_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        return self.volumes.update(volume_id, data)

    def delete_volume(self, volume_id: str) -> dict[str, Any]:
        return self.volumes.soft_delete(volume_id)

    def list_chapters(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.chapters.list(project_id=project_id, limit=limit, offset=offset)

    def create_chapter(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = project_id
        if data.get("volume_id"):
            volume = self.volumes.get(data["volume_id"])
            if volume["project_id"] != project_id:
                raise NovelValidationError("volume_id does not belong to project.")
        if data.get("chapter_index") is None:
            data["chapter_index"] = self.chapters.next_index("chapter_index", project_id=project_id)
        data["word_count"] = word_count_for(data.get("final_content") or data.get("draft_content"))
        return self.chapters.create(data)

    def get_chapter(self, chapter_id: str) -> dict[str, Any]:
        return self.chapters.get(chapter_id)

    def update_chapter(self, chapter_id: str, request: Any) -> dict[str, Any]:
        current = self.chapters.get(chapter_id)
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        if data.get("volume_id"):
            volume = self.volumes.get(data["volume_id"])
            if volume["project_id"] != current["project_id"]:
                raise NovelValidationError("volume_id does not belong to project.")
        draft = data.get("draft_content", current.get("draft_content"))
        final = data.get("final_content", current.get("final_content"))
        if "draft_content" in data or "final_content" in data:
            data["word_count"] = word_count_for(final or draft)
            data["version"] = int(current.get("version", 1)) + 1
        return self.chapters.update(chapter_id, data)

    def delete_chapter(self, chapter_id: str) -> dict[str, Any]:
        return self.chapters.soft_delete(chapter_id)

    def list_scenes(self, chapter_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        chapter = self.chapters.get(chapter_id)
        return self.scenes.list(parent_field="chapter_id", parent_id=chapter_id, project_id=chapter["project_id"], limit=limit, offset=offset)

    def create_scene(self, chapter_id: str, request: Any) -> dict[str, Any]:
        chapter = self.chapters.get(chapter_id)
        data = _model_dump(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = chapter["project_id"]
        data["chapter_id"] = chapter_id
        if data.get("scene_index") is None:
            data["scene_index"] = self.scenes.next_index("scene_index", project_id=chapter["project_id"], parent_field="chapter_id", parent_id=chapter_id)
        return self.scenes.create(data)

    def update_scene(self, scene_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        return self.scenes.update(scene_id, data)

    def delete_scene(self, scene_id: str) -> dict[str, Any]:
        return self.scenes.soft_delete(scene_id)

    def list_characters(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.characters.list(project_id=project_id, limit=limit, offset=offset)

    def create_character(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["name"] = _require_text(data.get("name"), "name")
        data["project_id"] = project_id
        return self.characters.create(data)

    def update_character(self, character_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "name" in data and data["name"] is not None:
            data["name"] = _require_text(data["name"], "name")
        return self.characters.update(character_id, data)

    def delete_character(self, character_id: str) -> dict[str, Any]:
        return self.characters.soft_delete(character_id)

    def list_world_entries(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.world_entries.list(project_id=project_id, limit=limit, offset=offset)

    def create_world_entry(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["category"] = _require_text(data.get("category"), "category")
        data["title"] = _require_text(data.get("title"), "title")
        data["content"] = _require_text(data.get("content"), "content")
        data["project_id"] = project_id
        return self.world_entries.create(data)

    def update_world_entry(self, entry_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        for field in ("category", "title", "content"):
            if field in data and data[field] is not None:
                data[field] = _require_text(data[field], field)
        return self.world_entries.update(entry_id, data)

    def delete_world_entry(self, entry_id: str) -> dict[str, Any]:
        return self.world_entries.soft_delete(entry_id)

    def list_plot_threads(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.plot_threads.list(project_id=project_id, limit=limit, offset=offset)

    def create_plot_thread(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = project_id
        return self.plot_threads.create(data)

    def update_plot_thread(self, thread_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        return self.plot_threads.update(thread_id, data)

    def delete_plot_thread(self, thread_id: str) -> dict[str, Any]:
        return self.plot_threads.soft_delete(thread_id)

    def list_timeline(self, project_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_project(project_id)
        return self.timeline.list(project_id=project_id, limit=limit, offset=offset)

    def create_timeline_event(self, project_id: str, request: Any) -> dict[str, Any]:
        self.get_project(project_id)
        data = _model_dump(request)
        data["title"] = _require_text(data.get("title"), "title")
        data["project_id"] = project_id
        if data.get("event_order") is None:
            data["event_order"] = self.timeline.next_index("event_order", project_id=project_id)
        return self.timeline.create(data)

    def update_timeline_event(self, event_id: str, request: Any) -> dict[str, Any]:
        data = _model_dump(request)
        if "title" in data and data["title"] is not None:
            data["title"] = _require_text(data["title"], "title")
        return self.timeline.update(event_id, data)

    def delete_timeline_event(self, event_id: str) -> dict[str, Any]:
        return self.timeline.soft_delete(event_id)
