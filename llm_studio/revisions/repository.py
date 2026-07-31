"""SQLite persistence for revision records and autosaves."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import RevisionConflictError, RevisionNotFoundError
from .migrations import initialize_revision_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _hash(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


class RevisionRecordRepository:
    def __init__(self, db_path: str | Path, *, autosave_retention: int = 20):
        self.db_path = Path(db_path)
        self.autosave_retention = max(1, int(autosave_retention or 20))
        self._lock = RLock()
        initialize_revision_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "generation_id": data.get("generation_id"),
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "original_text": data["original_text"],
            "edited_text": data["edited_text"],
            "diff_json": json.dumps(data.get("diff") or {}, ensure_ascii=False, sort_keys=True),
            "edit_tags_json": json.dumps(data.get("edit_tags") or [], ensure_ascii=False),
            "user_score": data.get("user_score"),
            "quality_notes": data.get("quality_notes"),
            "status": data.get("status", "draft"),
            "accepted_for_dataset": 1 if data.get("accepted_for_dataset") else 0,
            "reviewer_id": data.get("reviewer_id"),
            "source": data.get("source", "generation"),
            "original_hash": _hash(data["original_text"]),
            "edited_hash": _hash(data["edited_text"]),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO revision_records (
                    id, generation_id, project_id, chapter_id, scene_id,
                    original_text, edited_text, diff_json, edit_tags_json,
                    user_score, quality_notes, status, accepted_for_dataset,
                    reviewer_id, source, original_hash, edited_hash,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])

    def update(
        self,
        revision_id: str,
        changes: dict[str, Any],
        *,
        expected_updated_at: str | None = None,
    ) -> dict[str, Any]:
        current = self.get(revision_id)
        if expected_updated_at is not None and expected_updated_at != current["updated_at"]:
            raise RevisionConflictError("Revision has changed; refresh before saving.")

        allowed = {
            "edited_text",
            "diff",
            "edit_tags",
            "user_score",
            "quality_notes",
            "status",
            "accepted_for_dataset",
            "reviewer_id",
        }
        values: dict[str, Any] = {}
        for key, value in changes.items():
            if key not in allowed:
                continue
            if key == "diff":
                values["diff_json"] = json.dumps(value or {}, ensure_ascii=False, sort_keys=True)
            elif key == "edit_tags":
                values["edit_tags_json"] = json.dumps(value or [], ensure_ascii=False)
            elif key == "accepted_for_dataset":
                values[key] = 1 if value else 0
            else:
                values[key] = value
        if "edited_text" in values:
            values["edited_hash"] = _hash(values["edited_text"])
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE revision_records SET {assignments} WHERE id = ?",
                [*values.values(), revision_id],
            )
        if cursor.rowcount == 0:
            raise RevisionNotFoundError(revision_id)
        return self.get(revision_id)

    def get(self, revision_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM revision_records WHERE id = ?",
                (revision_id,),
            ).fetchone()
        if row is None:
            raise RevisionNotFoundError(revision_id)
        return self._revision_row(row)

    def list(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        generation_id: str | None = None,
        status: str | None = None,
        user_score: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("project_id", project_id),
            ("chapter_id", chapter_id),
            ("generation_id", generation_id),
            ("status", status),
            ("user_score", user_score),
        ):
            if value is not None and value != "":
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM revision_records{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._revision_row(row) for row in rows]

    def create_autosave(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "revision_id": data.get("revision_id"),
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "generation_id": data.get("generation_id"),
            "draft_text": data["draft_text"],
            "base_text_hash": data.get("base_text_hash"),
            "draft_hash": _hash(data["draft_text"]),
            "client_revision": int(data.get("client_revision") or 1),
            "created_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO revision_autosaves (
                    id, revision_id, project_id, chapter_id, generation_id,
                    draft_text, base_text_hash, draft_hash, client_revision,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
            if item["revision_id"]:
                conn.execute(
                    """
                    DELETE FROM revision_autosaves
                    WHERE revision_id = ?
                      AND id NOT IN (
                        SELECT id FROM revision_autosaves
                        WHERE revision_id = ?
                        ORDER BY created_at DESC
                        LIMIT ?
                      )
                    """,
                    (item["revision_id"], item["revision_id"], self.autosave_retention),
                )
        return self.get_autosave(item["id"])

    def get_autosave(self, autosave_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM revision_autosaves WHERE id = ?",
                (autosave_id,),
            ).fetchone()
        if row is None:
            raise RevisionNotFoundError(autosave_id)
        return self._autosave_row(row)

    def list_autosaves(self, revision_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM revision_autosaves
                WHERE revision_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (revision_id, max(1, min(limit, 200))),
            ).fetchall()
        return [self._autosave_row(row) for row in rows]

    @staticmethod
    def _revision_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["revision_id"] = data.pop("id")
        data["diff"] = _loads(data.pop("diff_json"), {})
        data["diff_json"] = data["diff"]
        data["edit_tags"] = _loads(data.pop("edit_tags_json"), [])
        data["accepted_for_dataset"] = bool(data["accepted_for_dataset"])
        return data

    @staticmethod
    def _autosave_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["autosave_id"] = data.pop("id")
        return data
