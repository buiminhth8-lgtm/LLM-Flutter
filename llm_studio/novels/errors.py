"""Novel Studio error types and codes."""

from __future__ import annotations

from dataclasses import dataclass

NOVEL_NOT_FOUND_CODES = {
    "project": "NOVEL_PROJECT_NOT_FOUND",
    "volume": "NOVEL_VOLUME_NOT_FOUND",
    "chapter": "NOVEL_CHAPTER_NOT_FOUND",
    "scene": "NOVEL_SCENE_NOT_FOUND",
    "character": "NOVEL_CHARACTER_NOT_FOUND",
    "world_entry": "NOVEL_WORLD_ENTRY_NOT_FOUND",
    "plot_thread": "NOVEL_PLOT_THREAD_NOT_FOUND",
    "timeline_event": "NOVEL_TIMELINE_EVENT_NOT_FOUND",
}


@dataclass
class NovelError(Exception):
    code: str
    message: str
    status_code: int = 400


class NovelNotFoundError(NovelError):
    def __init__(self, kind: str, item_id: str):
        super().__init__(
            code=NOVEL_NOT_FOUND_CODES.get(kind, "NOVEL_PROJECT_NOT_FOUND"),
            message=f"Novel {kind} not found: {item_id}",
            status_code=404,
        )


class NovelValidationError(NovelError):
    def __init__(self, message: str):
        super().__init__(code="NOVEL_VALIDATION_FAILED", message=message, status_code=400)


class NovelDuplicateSlugError(NovelError):
    def __init__(self, slug: str):
        super().__init__(
            code="NOVEL_DUPLICATE_SLUG",
            message=f"Novel project slug already exists: {slug}",
            status_code=409,
        )
