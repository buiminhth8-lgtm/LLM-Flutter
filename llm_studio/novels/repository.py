"""SQLite repositories for Novel Studio foundation data."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import NovelDuplicateSlugError, NovelNotFoundError
from .migrations import initialize_novel_database


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def word_count_for(text: str | None) -> int:
    if not text:
        return 0
    cjk = re.findall(r"[\u4e00-\u9fff]", text)
    words = re.findall(r"[A-Za-z0-9_]+", text)
    return len(cjk) + len(words)


class BaseNovelRepository:
    table = ""
    kind = ""
    allowed_update_fields: set[str] = set()

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_novel_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def get(self, item_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        query = f"SELECT * FROM {self.table} WHERE id = ?"
        params: list[Any] = [item_id]
        if not include_deleted and self._has_status():
            query += " AND status != 'deleted'"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            raise NovelNotFoundError(self.kind, item_id)
        return self._row_to_dict(row)

    def list(
        self,
        *,
        project_id: str | None = None,
        parent_field: str | None = None,
        parent_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if parent_field and parent_id:
            clauses.append(f"{parent_field} = ?")
            params.append(parent_id)
        if not include_deleted and self._has_status():
            clauses.append("status != 'deleted'")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        order = self._order_by()
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM {self.table}{where} {order} LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def update(self, item_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {k: v for k, v in changes.items() if k in self.allowed_update_fields}
        if not allowed:
            return self.get(item_id)
        allowed["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in allowed)
        params = [*allowed.values(), item_id]
        with self._lock, self._connect() as conn:
            cursor = conn.execute(f"UPDATE {self.table} SET {assignments} WHERE id = ?", params)
        if cursor.rowcount == 0:
            raise NovelNotFoundError(self.kind, item_id)
        return self.get(item_id)

    def soft_delete(self, item_id: str) -> dict[str, Any]:
        if not self._has_status():
            raise NovelNotFoundError(self.kind, item_id)
        now = utc_now()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE {self.table} SET status = 'deleted', updated_at = ? WHERE id = ?",
                (now, item_id),
            )
        if cursor.rowcount == 0:
            raise NovelNotFoundError(self.kind, item_id)
        return self.get(item_id, include_deleted=True)

    def next_index(self, field: str, *, project_id: str | None = None, parent_field: str | None = None, parent_id: str | None = None) -> int:
        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if parent_field and parent_id:
            clauses.append(f"{parent_field} = ?")
            params.append(parent_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            value = conn.execute(f"SELECT COALESCE(MAX({field}), 0) + 1 FROM {self.table}{where}", params).fetchone()[0]
        return int(value)

    def _row_to_dict(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        if "metadata_json" in data:
            try:
                data["metadata"] = json.loads(data["metadata_json"] or "{}")
            except json.JSONDecodeError:
                data["metadata"] = {}
        return data

    def _has_status(self) -> bool:
        return True

    def _order_by(self) -> str:
        if self.table == "novel_volumes":
            return "ORDER BY volume_index ASC, created_at ASC"
        if self.table == "novel_chapters":
            return "ORDER BY chapter_index ASC, created_at ASC"
        if self.table == "novel_scenes":
            return "ORDER BY scene_index ASC, created_at ASC"
        if self.table == "novel_timeline_events":
            return "ORDER BY event_order ASC, created_at ASC"
        return "ORDER BY updated_at DESC"


class NovelProjectRepository(BaseNovelRepository):
    table = "novel_projects"
    kind = "project"
    allowed_update_fields = {"title", "genre", "description", "target_style", "target_audience", "status", "metadata_json"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "title": data["title"],
            "slug": data["slug"],
            "genre": data.get("genre"),
            "description": data.get("description"),
            "target_style": data.get("target_style"),
            "target_audience": data.get("target_audience"),
            "status": data.get("status", "active"),
            "metadata_json": json.dumps(data.get("metadata") or {}, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO novel_projects (
                        id, title, slug, genre, description, target_style,
                        target_audience, status, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tuple(item.values()),
                )
        except sqlite3.IntegrityError as exc:
            raise NovelDuplicateSlugError(item["slug"]) from exc
        return self.get(item["id"])


class NovelVolumeRepository(BaseNovelRepository):
    table = "novel_volumes"
    kind = "volume"
    allowed_update_fields = {"title", "volume_index", "outline", "status"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "title": data["title"],
            "volume_index": int(data["volume_index"]),
            "outline": data.get("outline"),
            "status": data.get("status", "active"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_volumes (
                    id, project_id, title, volume_index, outline, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelChapterRepository(BaseNovelRepository):
    table = "novel_chapters"
    kind = "chapter"
    allowed_update_fields = {"volume_id", "title", "chapter_index", "outline", "draft_content", "final_content", "summary", "word_count", "status", "version"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "volume_id": data.get("volume_id"),
            "title": data["title"],
            "chapter_index": int(data["chapter_index"]),
            "outline": data.get("outline"),
            "draft_content": data.get("draft_content"),
            "final_content": data.get("final_content"),
            "summary": data.get("summary"),
            "word_count": int(data.get("word_count", 0)),
            "status": data.get("status", "outline"),
            "version": int(data.get("version", 1)),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_chapters (
                    id, project_id, volume_id, title, chapter_index, outline,
                    draft_content, final_content, summary, word_count, status,
                    version, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelSceneRepository(BaseNovelRepository):
    table = "novel_scenes"
    kind = "scene"
    allowed_update_fields = {"title", "scene_index", "outline", "content", "pov_character_id", "location", "timeline_note", "status"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "chapter_id": data["chapter_id"],
            "title": data["title"],
            "scene_index": int(data["scene_index"]),
            "outline": data.get("outline"),
            "content": data.get("content"),
            "pov_character_id": data.get("pov_character_id"),
            "location": data.get("location"),
            "timeline_note": data.get("timeline_note"),
            "status": data.get("status", "outline"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_scenes (
                    id, project_id, chapter_id, title, scene_index, outline, content,
                    pov_character_id, location, timeline_note, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelCharacterRepository(BaseNovelRepository):
    table = "novel_characters"
    kind = "character"
    allowed_update_fields = {"name", "aliases", "role", "personality", "background", "goals", "relationships", "speech_style", "appearance", "notes", "status"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "name": data["name"],
            "aliases": data.get("aliases"),
            "role": data.get("role"),
            "personality": data.get("personality"),
            "background": data.get("background"),
            "goals": data.get("goals"),
            "relationships": data.get("relationships"),
            "speech_style": data.get("speech_style"),
            "appearance": data.get("appearance"),
            "notes": data.get("notes"),
            "status": data.get("status", "active"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_characters (
                    id, project_id, name, aliases, role, personality, background,
                    goals, relationships, speech_style, appearance, notes, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelWorldEntryRepository(BaseNovelRepository):
    table = "novel_world_entries"
    kind = "world_entry"
    allowed_update_fields = {"category", "title", "content", "tags", "priority", "status"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "category": data["category"],
            "title": data["title"],
            "content": data["content"],
            "tags": data.get("tags"),
            "priority": int(data.get("priority", 0)),
            "status": data.get("status", "active"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_world_entries (
                    id, project_id, category, title, content, tags, priority,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelPlotThreadRepository(BaseNovelRepository):
    table = "novel_plot_threads"
    kind = "plot_thread"
    allowed_update_fields = {"title", "description", "status", "priority", "related_character_ids"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "title": data["title"],
            "description": data.get("description"),
            "status": data.get("status", "open"),
            "priority": int(data.get("priority", 0)),
            "related_character_ids": data.get("related_character_ids"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_plot_threads (
                    id, project_id, title, description, status, priority,
                    related_character_ids, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])


class NovelTimelineRepository(BaseNovelRepository):
    table = "novel_timeline_events"
    kind = "timeline_event"
    allowed_update_fields = {"title", "event_order", "chapter_id", "scene_id", "description", "involved_character_ids", "status"}

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "project_id": data["project_id"],
            "title": data["title"],
            "event_order": int(data["event_order"]),
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "description": data.get("description"),
            "involved_character_ids": data.get("involved_character_ids"),
            "status": data.get("status", "active"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO novel_timeline_events (
                    id, project_id, title, event_order, chapter_id, scene_id,
                    description, involved_character_ids, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])
