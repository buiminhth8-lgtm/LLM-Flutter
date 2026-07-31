"""SQLite persistence for model generation records."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import WritingNotFoundError
from .migrations import initialize_writing_database

_JSON_FIELDS = {
    "input_context_json": ("input_context", {}),
    "generation_params_json": ("generation_params", {}),
    "target_length_json": ("target_length", {}),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class GenerationRecordRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_writing_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "project_id": data["project_id"],
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": data.get("template_id"),
            "template_version_id": data.get("template_version_id"),
            "context_id": data.get("context_id"),
            "model_id": data["model_id"],
            "adapter_id": data.get("adapter_id"),
            "mode": data["mode"],
            "prompt_rendered": data["prompt_rendered"],
            "input_context_json": json.dumps(data.get("input_context") or {}, ensure_ascii=False),
            "model_output": data.get("model_output") or "",
            "generation_params_json": json.dumps(data.get("generation_params") or {}, ensure_ascii=False),
            "target_length_json": json.dumps(data.get("target_length") or {}, ensure_ascii=False),
            "status": data.get("status", "created"),
            "finish_reason": data.get("finish_reason"),
            "prompt_hash": data.get("prompt_hash"),
            "context_hash": data.get("context_hash"),
            "output_hash": data.get("output_hash"),
            "input_token_estimate": int(data.get("input_token_estimate") or 0),
            "output_token_estimate": int(data.get("output_token_estimate") or 0),
            "output_char_count": int(data.get("output_char_count") or 0),
            "latency_ms": data.get("latency_ms"),
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO generation_records (
                    id, project_id, chapter_id, scene_id, template_id,
                    template_version_id, context_id, model_id, adapter_id, mode,
                    prompt_rendered, input_context_json, model_output,
                    generation_params_json, target_length_json, status,
                    finish_reason, prompt_hash, context_hash, output_hash,
                    input_token_estimate, output_token_estimate,
                    output_char_count, latency_ms, error_code, error_message,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                tuple(item.values()),
            )
        return self.get(item["id"])

    def update(self, generation_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed = {
            "model_output",
            "status",
            "finish_reason",
            "output_hash",
            "output_token_estimate",
            "output_char_count",
            "latency_ms",
            "error_code",
            "error_message",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return self.get(generation_id)
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE generation_records SET {assignments} WHERE id = ?",
                [*values.values(), generation_id],
            )
        if cursor.rowcount == 0:
            raise WritingNotFoundError("generation", generation_id)
        return self.get(generation_id)

    def get(self, generation_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM generation_records WHERE id = ?",
                (generation_id,),
            ).fetchone()
        if row is None:
            raise WritingNotFoundError("generation", generation_id)
        return self._row(row)

    def list(
        self,
        *,
        project_id: str | None = None,
        chapter_id: str | None = None,
        mode: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("project_id", project_id),
            ("chapter_id", chapter_id),
            ("mode", mode),
            ("status", status),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM generation_records{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._row(row) for row in rows]

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["generation_id"] = data.pop("id")
        for storage_name, (public_name, fallback) in _JSON_FIELDS.items():
            data[public_name] = _loads(data.pop(storage_name), fallback)
        return data
