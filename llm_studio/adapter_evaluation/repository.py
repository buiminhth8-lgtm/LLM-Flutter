"""SQLite persistence for Novel Studio Stage 9 Adapter Evaluation."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    AdapterEvalCaseNotFoundError,
    AdapterEvalReportNotFoundError,
    AdapterEvalResultNotFoundError,
    AdapterEvalScoreNotFoundError,
    AdapterEvalSessionNotFoundError,
)
from .migrations import initialize_adapter_evaluation_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, sort_keys=True)


class AdapterEvaluationRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_adapter_evaluation_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_session(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "name": data["name"],
            "description": data.get("description"),
            "project_id": data.get("project_id"),
            "finetune_run_id": data.get("finetune_run_id"),
            "dataset_version_id": data.get("dataset_version_id"),
            "base_model_id": data["base_model_id"],
            "adapter_id": data["adapter_id"],
            "status": data.get("status", "draft"),
            "metadata_json": _json(data.get("metadata")),
            "created_by": data.get("created_by"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO adapter_evaluation_sessions (
                  id, name, description, project_id, finetune_run_id,
                  dataset_version_id, base_model_id, adapter_id, status,
                  metadata_json, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_session(item["id"])

    def update_session(self, session_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get_session(session_id)
        allowed = {
            "name",
            "description",
            "status",
            "metadata_json",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE adapter_evaluation_sessions SET {assignments} WHERE id = ?",
                [*values.values(), session_id],
            )
        if cursor.rowcount == 0:
            raise AdapterEvalSessionNotFoundError(session_id)
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            raise AdapterEvalSessionNotFoundError(session_id)
        return self._session_row(row)

    def list_sessions(
        self,
        *,
        status: str | None = None,
        project_id: str | None = None,
        adapter_id: str | None = None,
        finetune_run_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("status", status),
            ("project_id", project_id),
            ("adapter_id", adapter_id),
            ("finetune_run_id", finetune_run_id),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM adapter_evaluation_sessions{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._session_row(row) for row in rows]

    def create_case(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "session_id": data["session_id"],
            "project_id": data.get("project_id"),
            "chapter_id": data.get("chapter_id"),
            "scene_id": data.get("scene_id"),
            "template_id": data.get("template_id"),
            "template_version_id": data.get("template_version_id"),
            "context_id": data.get("context_id"),
            "mode": data["mode"],
            "title": data["title"],
            "user_variables_json": _json(data.get("user_variables")),
            "generation_params_json": _json(data.get("generation_params")),
            "target_length_json": _json(data.get("target_length")),
            "prompt_rendered": data.get("prompt_rendered"),
            "context_snapshot_json": _json(data.get("context_snapshot")),
            "prompt_hash": data.get("prompt_hash"),
            "context_hash": data.get("context_hash"),
            "status": data.get("status", "pending"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO adapter_evaluation_cases (
                  id, session_id, project_id, chapter_id, scene_id, template_id,
                  template_version_id, context_id, mode, title,
                  user_variables_json, generation_params_json, target_length_json,
                  prompt_rendered, context_snapshot_json, prompt_hash, context_hash,
                  status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_case(item["id"])

    def update_case(self, case_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get_case(case_id)
        allowed = {
            "context_id",
            "template_id",
            "template_version_id",
            "prompt_rendered",
            "context_snapshot_json",
            "prompt_hash",
            "context_hash",
            "status",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE adapter_evaluation_cases SET {assignments} WHERE id = ?",
                [*values.values(), case_id],
            )
        if cursor.rowcount == 0:
            raise AdapterEvalCaseNotFoundError(case_id)
        return self.get_case(case_id)

    def get_case(self, case_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_cases WHERE id = ?",
                (case_id,),
            ).fetchone()
        if row is None:
            raise AdapterEvalCaseNotFoundError(case_id)
        return self._case_row(row)

    def list_cases(
        self,
        session_id: str,
        *,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self.get_session(session_id)
        clauses = ["session_id = ?"]
        params: list[Any] = [session_id]
        if status:
            clauses.append("status = ?")
            params.append(status)
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM adapter_evaluation_cases WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at ASC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._case_row(row) for row in rows]

    def upsert_result(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        existing = self._get_result_for_case_variant(data["case_id"], data["variant"])
        item = {
            "id": existing["result_id"] if existing else data.get("id") or str(uuid.uuid4()),
            "case_id": data["case_id"],
            "session_id": data["session_id"],
            "variant": data["variant"],
            "model_id": data["model_id"],
            "adapter_id": data.get("adapter_id"),
            "output_text": data.get("output_text") or "",
            "generation_record_id": data.get("generation_record_id"),
            "status": data.get("status", "created"),
            "finish_reason": data.get("finish_reason"),
            "output_hash": data.get("output_hash"),
            "output_char_count": int(data.get("output_char_count") or 0),
            "output_token_estimate": int(data.get("output_token_estimate") or 0),
            "latency_ms": data.get("latency_ms"),
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message"),
            "created_at": existing["created_at"] if existing else data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            if existing:
                conn.execute(
                    """
                    UPDATE adapter_evaluation_results
                    SET model_id = ?, adapter_id = ?, output_text = ?,
                        generation_record_id = ?, status = ?, finish_reason = ?,
                        output_hash = ?, output_char_count = ?,
                        output_token_estimate = ?, latency_ms = ?, error_code = ?,
                        error_message = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        item["model_id"],
                        item["adapter_id"],
                        item["output_text"],
                        item["generation_record_id"],
                        item["status"],
                        item["finish_reason"],
                        item["output_hash"],
                        item["output_char_count"],
                        item["output_token_estimate"],
                        item["latency_ms"],
                        item["error_code"],
                        item["error_message"],
                        item["updated_at"],
                        item["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO adapter_evaluation_results (
                      id, case_id, session_id, variant, model_id, adapter_id,
                      output_text, generation_record_id, status, finish_reason,
                      output_hash, output_char_count, output_token_estimate,
                      latency_ms, error_code, error_message, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tuple(item.values()),
                )
        return self.get_result(item["id"])

    def get_result(self, result_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_results WHERE id = ?",
                (result_id,),
            ).fetchone()
        if row is None:
            raise AdapterEvalResultNotFoundError(result_id)
        return self._result_row(row)

    def list_results(
        self,
        *,
        case_id: str | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if case_id:
            clauses.append("case_id = ?")
            params.append(case_id)
        if session_id:
            clauses.append("session_id = ?")
            params.append(session_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM adapter_evaluation_results{where} ORDER BY variant ASC",
                params,
            ).fetchall()
        return [self._result_row(row) for row in rows]

    def upsert_score(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        existing = self.get_score_for_case(data["case_id"], required=False)
        item = {
            "id": existing["score_id"] if existing else data.get("id") or str(uuid.uuid4()),
            "case_id": data["case_id"],
            "session_id": data["session_id"],
            "base_result_id": data.get("base_result_id"),
            "adapter_result_id": data.get("adapter_result_id"),
            "winner": data.get("winner"),
            "base_score": data.get("base_score"),
            "adapter_score": data.get("adapter_score"),
            "dimensions_json": _json(data.get("dimensions")),
            "notes": data.get("notes"),
            "reviewer_id": data.get("reviewer_id"),
            "created_at": existing["created_at"] if existing else data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            if existing:
                conn.execute(
                    """
                    UPDATE adapter_evaluation_scores
                    SET base_result_id = ?, adapter_result_id = ?, winner = ?,
                        base_score = ?, adapter_score = ?, dimensions_json = ?,
                        notes = ?, reviewer_id = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        item["base_result_id"],
                        item["adapter_result_id"],
                        item["winner"],
                        item["base_score"],
                        item["adapter_score"],
                        item["dimensions_json"],
                        item["notes"],
                        item["reviewer_id"],
                        item["updated_at"],
                        item["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO adapter_evaluation_scores (
                      id, case_id, session_id, base_result_id, adapter_result_id,
                      winner, base_score, adapter_score, dimensions_json, notes,
                      reviewer_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tuple(item.values()),
                )
        return self.get_score(item["id"])

    def get_score(self, score_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_scores WHERE id = ?",
                (score_id,),
            ).fetchone()
        if row is None:
            raise AdapterEvalScoreNotFoundError(score_id)
        return self._score_row(row)

    def get_score_for_case(
        self,
        case_id: str,
        *,
        required: bool = True,
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_scores WHERE case_id = ?",
                (case_id,),
            ).fetchone()
        if row is None:
            if required:
                raise AdapterEvalScoreNotFoundError(case_id)
            return None
        return self._score_row(row)

    def list_scores(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM adapter_evaluation_scores WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [self._score_row(row) for row in rows]

    def create_report(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "session_id": data["session_id"],
            "report_json": json.dumps(
                data.get("report") or {},
                ensure_ascii=False,
                sort_keys=True,
            ),
            "summary_text": data.get("summary_text"),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO adapter_evaluation_reports (
                  id, session_id, report_json, summary_text, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_report(item["id"])

    def get_report(self, report_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM adapter_evaluation_reports WHERE id = ?",
                (report_id,),
            ).fetchone()
        if row is None:
            raise AdapterEvalReportNotFoundError(report_id)
        return self._report_row(row)

    def list_reports(self, session_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_session(session_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM adapter_evaluation_reports
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (session_id, max(1, min(limit, 200)), max(0, offset)),
            ).fetchall()
        return [self._report_row(row) for row in rows]

    def _get_result_for_case_variant(
        self,
        case_id: str,
        variant: str,
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM adapter_evaluation_results
                WHERE case_id = ? AND variant = ?
                """,
                (case_id, variant),
            ).fetchone()
        return self._result_row(row) if row else None

    @staticmethod
    def _session_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["session_id"] = data.pop("id")
        data["metadata"] = _loads(data.pop("metadata_json"), {})
        return data

    @staticmethod
    def _case_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["case_id"] = data.pop("id")
        data["user_variables"] = _loads(data.pop("user_variables_json"), {})
        data["generation_params"] = _loads(data.pop("generation_params_json"), {})
        data["target_length"] = _loads(data.pop("target_length_json"), {})
        data["context_snapshot"] = _loads(data.pop("context_snapshot_json"), {})
        return data

    @staticmethod
    def _result_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["result_id"] = data.pop("id")
        return data

    @staticmethod
    def _score_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["score_id"] = data.pop("id")
        data["dimensions"] = _loads(data.pop("dimensions_json"), {})
        return data

    @staticmethod
    def _report_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["report_id"] = data.pop("id")
        data["report"] = _loads(data.pop("report_json"), {})
        return data
