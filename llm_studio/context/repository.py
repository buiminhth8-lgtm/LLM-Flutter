"""SQLite repository for Context Assembler records."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import ContextNotFoundError
from .migrations import initialize_context_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class ContextAssemblyRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_context_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        item = {
            "id": str(uuid.uuid4()),
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": data.get("template_id"),
            "template_version_id": data.get("template_version_id"),
            "mode": data["mode"],
            "budget_json": json.dumps(data.get("budget") or {}, ensure_ascii=False),
            "variables_json": json.dumps(data.get("variables") or {}, ensure_ascii=False),
            "selected_items_json": json.dumps(data.get("selected_items") or {}, ensure_ascii=False),
            "warnings_json": json.dumps(data.get("warnings") or [], ensure_ascii=False),
            "estimated_tokens": int(data.get("estimated_tokens") or 0),
            "estimated_chars": int(data.get("estimated_chars") or 0),
            "context_hash": data["context_hash"],
            "retrieval_id": data.get("retrieval_id"),
            "created_at": _now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO context_assembly_records (
                    id, project_id, chapter_id, scene_id, template_id,
                    template_version_id, mode, budget_json, variables_json,
                    selected_items_json, warnings_json, estimated_tokens,
                    estimated_chars, context_hash, retrieval_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])

    def get(self, context_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM context_assembly_records WHERE id = ?",
                (context_id,),
            ).fetchone()
        if row is None:
            raise ContextNotFoundError("context", context_id)
        return self._row(row)

    def list(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if chapter_id:
            clauses.append("chapter_id = ?")
            params.append(chapter_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM context_assembly_records{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["context_id"] = data.pop("id")
        data["budget"] = _loads(data.pop("budget_json"), {})
        data["variables"] = _loads(data.pop("variables_json"), {})
        data["selected_items"] = _loads(data.pop("selected_items_json"), {})
        data["warnings"] = _loads(data.pop("warnings_json"), [])
        return data
