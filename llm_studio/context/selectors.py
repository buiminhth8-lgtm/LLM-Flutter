"""Deterministic selectors for Novel Studio context material."""

from __future__ import annotations

import json
from typing import Any


def parse_id_list(value: Any) -> set[str]:
    if value in (None, ""):
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value if str(item).strip()}
    text = str(value).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = [part.strip() for part in text.split(",")]
    if isinstance(parsed, list):
        return {str(item) for item in parsed if str(item).strip()}
    return set()


class CharacterSelector:
    def select(
        self,
        characters: list[dict[str, Any]],
        *,
        pov_character_id: str | None = None,
        related_character_ids: set[str] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        related = related_character_ids or set()
        main_roles = {"protagonist", "main", "主角", "主要人物"}

        def rank(item: dict[str, Any]) -> tuple[int, str]:
            item_id = str(item.get("id") or "")
            role = str(item.get("role") or "").strip().lower()
            if item_id and item_id == pov_character_id:
                priority = 0
            elif item_id in related:
                priority = 1
            elif role in main_roles:
                priority = 2
            else:
                priority = 3
            return priority, str(item.get("name") or "")

        return sorted(characters, key=rank)[: max(0, limit)]


class WorldEntrySelector:
    _category_rank = {
        "world_rule": 0,
        "cultivation_system": 1,
        "location": 2,
        "faction": 3,
    }

    def select(
        self,
        entries: list[dict[str, Any]],
        *,
        scene_location: str | None = None,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        location = (scene_location or "").strip().lower()

        def rank(item: dict[str, Any]) -> tuple[int, int, int, str]:
            title = str(item.get("title") or "").strip().lower()
            location_match = 0 if location and (location in title or title in location) else 1
            category = str(item.get("category") or "")
            return (
                location_match,
                -int(item.get("priority") or 0),
                self._category_rank.get(category, 9),
                title,
            )

        return sorted(entries, key=rank)[: max(0, limit)]


class PlotThreadSelector:
    def select(
        self,
        threads: list[dict[str, Any]],
        *,
        selected_character_ids: set[str] | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        selected = selected_character_ids or set()
        status_rank = {"in_progress": 0, "open": 1}

        def rank(item: dict[str, Any]) -> tuple[int, int, int, str]:
            related = parse_id_list(item.get("related_character_ids"))
            intersects = 0 if selected.intersection(related) else 1
            return (
                status_rank.get(str(item.get("status") or ""), 5),
                intersects,
                -int(item.get("priority") or 0),
                str(item.get("title") or ""),
            )

        active = [item for item in threads if item.get("status") in {"open", "in_progress"}]
        return sorted(active, key=rank)[: max(0, limit)]


class TimelineSelector:
    def select(
        self,
        events: list[dict[str, Any]],
        *,
        current_chapter_id: str | None = None,
        current_scene_id: str | None = None,
        current_chapter_index: int | None = None,
        chapter_indexes: dict[str, int] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        indexes = chapter_indexes or {}
        eligible: list[dict[str, Any]] = []
        for item in events:
            chapter_id = item.get("chapter_id")
            chapter_index = indexes.get(str(chapter_id)) if chapter_id else None
            if (
                current_chapter_index is not None
                and chapter_index is not None
                and chapter_index > current_chapter_index
            ):
                continue
            eligible.append(item)

        def rank(item: dict[str, Any]) -> tuple[int, int]:
            directly_related = (
                item.get("scene_id") == current_scene_id
                or item.get("chapter_id") == current_chapter_id
            )
            return (0 if directly_related else 1, -int(item.get("event_order") or 0))

        selected = sorted(eligible, key=rank)[: max(0, limit)]
        return sorted(selected, key=lambda item: int(item.get("event_order") or 0))


class PreviousChapterSelector:
    def select(
        self,
        chapters: list[dict[str, Any]],
        current_chapter: dict[str, Any] | None,
        *,
        fallback_chars: int = 1200,
    ) -> tuple[dict[str, Any] | None, str, list[dict[str, Any]]]:
        if not current_chapter:
            return None, "", []
        current_index = int(current_chapter.get("chapter_index") or 0)
        previous = next(
            (
                item
                for item in chapters
                if int(item.get("chapter_index") or 0) == current_index - 1
            ),
            None,
        )
        if previous is None:
            return None, "", []
        summary = str(previous.get("summary") or "").strip()
        warnings: list[dict[str, Any]] = []
        if not summary:
            content = str(previous.get("final_content") or "").strip()
            if content:
                summary = content[:fallback_chars]
                warnings.append(
                    {
                        "code": "CONTEXT_PREVIOUS_SUMMARY_FALLBACK",
                        "message": "上一章没有摘要，已使用正文片段作为上下文。",
                        "affected": ["previous_chapter_summary"],
                    }
                )
        return previous, summary, warnings


class SceneSelector:
    def select(self, scenes: list[dict[str, Any]], scene_id: str | None) -> dict[str, Any] | None:
        if not scene_id:
            return None
        return next((item for item in scenes if item.get("id") == scene_id), None)
