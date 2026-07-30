"""SQLite repositories for Prompt Studio."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import PromptNotFoundError, PromptVersionMismatchError
from .migrations import initialize_prompt_database


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def _loads(value: str | None, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class BasePromptRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_prompt_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


class PromptTemplateRepository(BasePromptRepository):
    def create_template(self, data: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        item = {
            "id": new_id(),
            "name": data["name"],
            "type": data["type"],
            "description": data.get("description"),
            "scope": data.get("scope", "global"),
            "project_id": data.get("project_id"),
            "active_version_id": None,
            "status": data.get("status", "active"),
            "metadata_json": json.dumps(data.get("metadata") or {}, ensure_ascii=False),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prompt_templates (
                    id, name, type, description, scope, project_id,
                    active_version_id, status, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_template(item["id"])

    def list_templates(
        self,
        *,
        type: str | None = None,
        scope: str | None = None,
        project_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if type:
            clauses.append("type = ?")
            params.append(type)
        if scope:
            clauses.append("scope = ?")
            params.append(scope)
        if project_id:
            clauses.append("project_id = ?")
            params.append(project_id)
        if not include_deleted:
            clauses.append("status != 'deleted'")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM prompt_templates{where} ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._template_row(row) for row in rows]

    def get_template(self, template_id: str, *, include_deleted: bool = False) -> dict[str, Any]:
        query = "SELECT * FROM prompt_templates WHERE id = ?"
        params: list[Any] = [template_id]
        if not include_deleted:
            query += " AND status != 'deleted'"
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        if row is None:
            raise PromptNotFoundError("template", template_id)
        return self._template_row(row)

    def update_template_metadata(self, template_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = {"name", "type", "description", "scope", "project_id", "status", "metadata_json"}
        allowed = {key: value for key, value in changes.items() if key in allowed_keys}
        if not allowed:
            return self.get_template(template_id)
        allowed["updated_at"] = utc_now()
        assignments = ", ".join(f"{key} = ?" for key in allowed)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE prompt_templates SET {assignments} WHERE id = ?",
                [*allowed.values(), template_id],
            )
        if cursor.rowcount == 0:
            raise PromptNotFoundError("template", template_id)
        return self.get_template(template_id)

    def activate_version(self, template_id: str, version_id: str) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            version = conn.execute(
                "SELECT id FROM prompt_template_versions WHERE id = ? AND template_id = ?",
                (version_id, template_id),
            ).fetchone()
            if version is None:
                raise PromptVersionMismatchError("Version does not belong to template.")
            cursor = conn.execute(
                "UPDATE prompt_templates SET active_version_id = ?, updated_at = ? WHERE id = ?",
                (version_id, utc_now(), template_id),
            )
        if cursor.rowcount == 0:
            raise PromptNotFoundError("template", template_id)
        return self.get_template(template_id)

    def soft_delete_template(self, template_id: str) -> dict[str, Any]:
        return self.update_template_metadata(template_id, {"status": "deleted"})

    def _template_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metadata"] = _loads(data.pop("metadata_json", "{}"), {})
        return data


class PromptTemplateVersionRepository(BasePromptRepository):
    def create_version(self, template_id: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            current = conn.execute(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM prompt_template_versions WHERE template_id = ?",
                (template_id,),
            ).fetchone()[0]
            item = {
                "id": new_id(),
                "template_id": template_id,
                "version": int(current),
                "system_prompt": data.get("system_prompt"),
                "role_prompt": data.get("role_prompt"),
                "instruction_template": data["instruction_template"],
                "negative_prompt": data.get("negative_prompt"),
                "output_constraints": data.get("output_constraints"),
                "variables_schema_json": json.dumps(data.get("variables_schema") or {}, ensure_ascii=False),
                "default_values_json": json.dumps(data.get("default_values") or {}, ensure_ascii=False),
                "renderer": data.get("renderer", "simple_mustache"),
                "change_note": data.get("change_note"),
                "created_at": utc_now(),
            }
            conn.execute(
                """
                INSERT INTO prompt_template_versions (
                    id, template_id, version, system_prompt, role_prompt,
                    instruction_template, negative_prompt, output_constraints,
                    variables_schema_json, default_values_json, renderer,
                    change_note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_version(item["id"])

    def list_versions(self, template_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM prompt_template_versions WHERE template_id = ? ORDER BY version DESC",
                (template_id,),
            ).fetchall()
        return [self._version_row(row) for row in rows]

    def get_version(self, version_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM prompt_template_versions WHERE id = ?", (version_id,)).fetchone()
        if row is None:
            raise PromptNotFoundError("version", version_id)
        return self._version_row(row)

    def latest_for_template(self, template_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM prompt_template_versions WHERE template_id = ? ORDER BY version DESC LIMIT 1",
                (template_id,),
            ).fetchone()
        if row is None:
            raise PromptNotFoundError("version", template_id)
        return self._version_row(row)

    def _version_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["variables_schema"] = _loads(data.pop("variables_schema_json", "{}"), {})
        data["default_values"] = _loads(data.pop("default_values_json", "{}"), {})
        return data


class PromptRenderRecordRepository(BasePromptRepository):
    def save_render_record(self, data: dict[str, Any]) -> dict[str, Any]:
        item = {
            "id": new_id(),
            "template_id": data["template_id"],
            "template_version_id": data["template_version_id"],
            "project_id": data.get("project_id"),
            "chapter_id": data.get("chapter_id"),
            "variables_json": json.dumps(data.get("variables") or {}, ensure_ascii=False),
            "rendered_prompt": data["rendered_prompt"],
            "missing_variables_json": json.dumps(data.get("missing_variables") or [], ensure_ascii=False),
            "warnings_json": json.dumps(data.get("warnings") or [], ensure_ascii=False),
            "prompt_hash": data["prompt_hash"],
            "created_at": utc_now(),
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO prompt_render_records (
                    id, template_id, template_version_id, project_id, chapter_id,
                    variables_json, rendered_prompt, missing_variables_json,
                    warnings_json, prompt_hash, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_render_record(item["id"])

    def get_render_record(self, render_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM prompt_render_records WHERE id = ?", (render_id,)).fetchone()
        if row is None:
            raise PromptNotFoundError("version", render_id)
        return self._render_row(row)

    def list_render_records(self, *, template_id: str | None = None, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if template_id:
            clauses.append("template_id = ?")
            params.append(template_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM prompt_render_records{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._render_row(row) for row in rows]

    def _render_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["variables"] = _loads(data.pop("variables_json", "{}"), {})
        data["missing_variables"] = _loads(data.pop("missing_variables_json", "[]"), [])
        data["warnings"] = _loads(data.pop("warnings_json", "[]"), [])
        return data
