"""SQLite persistence for Stage 11 Evaluation Center."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    EvaluationCaseNotFoundError,
    EvaluationFindingNotFoundError,
    EvaluationReportNotFoundError,
    EvaluationRunNotFoundError,
)
from .migrations import initialize_evaluation_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def _json(value: Any, fallback: Any) -> str:
    return json.dumps(value if value is not None else fallback, ensure_ascii=False, sort_keys=True)


class EvaluationRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_evaluation_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_run(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "name": data["name"],
            "description": data.get("description"),
            "project_id": data.get("project_id"),
            "chapter_id": data.get("chapter_id"),
            "generation_id": data.get("generation_id"),
            "revision_id": data.get("revision_id"),
            "adapter_eval_session_id": data.get("adapter_eval_session_id"),
            "memory_retrieval_id": data.get("memory_retrieval_id"),
            "target_type": data["target_type"],
            "target_id": data["target_id"],
            "status": data.get("status", "created"),
            "evaluator_config_json": _json(data.get("evaluator_config"), {}),
            "overall_score": data.get("overall_score"),
            "summary_text": data.get("summary_text"),
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message"),
            "job_id": data.get("job_id"),
            "created_by": data.get("created_by"),
            "started_at": data.get("started_at"),
            "finished_at": data.get("finished_at"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_runs (
                  id, name, description, project_id, chapter_id, generation_id,
                  revision_id, adapter_eval_session_id, memory_retrieval_id,
                  target_type, target_id, status, evaluator_config_json,
                  overall_score, summary_text, error_code, error_message, job_id,
                  created_by, started_at, finished_at, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_run(item["id"])

    def update_run(self, run_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        self.get_run(run_id)
        allowed = {
            "name",
            "description",
            "status",
            "overall_score",
            "summary_text",
            "error_code",
            "error_message",
            "job_id",
            "started_at",
            "finished_at",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if "evaluator_config" in changes:
            values["evaluator_config_json"] = _json(changes["evaluator_config"], {})
        if not values:
            return self.get_run(run_id)
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE evaluation_runs SET {assignments} WHERE id = ?",
                [*values.values(), run_id],
            )
        if cursor.rowcount == 0:
            raise EvaluationRunNotFoundError(run_id)
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM evaluation_runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise EvaluationRunNotFoundError(run_id)
        return self._run_row(row)

    def list_runs(
        self,
        *,
        project_id: str | None = None,
        target_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("project_id", project_id),
            ("target_type", target_type),
            ("status", status),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM evaluation_runs{where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._run_row(row) for row in rows]

    def create_case(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "project_id": data.get("project_id"),
            "chapter_id": data.get("chapter_id"),
            "target_type": data["target_type"],
            "target_id": data["target_id"],
            "evaluator_type": data["evaluator_type"],
            "input_snapshot_json": _json(data.get("input_snapshot"), {}),
            "status": data.get("status", "pending"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_cases (
                  id, run_id, project_id, chapter_id, target_type, target_id,
                  evaluator_type, input_snapshot_json, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_case(item["id"])

    def update_case(self, case_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        self.get_case(case_id)
        values = {key: value for key, value in changes.items() if key in {"status"}}
        if "input_snapshot" in changes:
            values["input_snapshot_json"] = _json(changes["input_snapshot"], {})
        if not values:
            return self.get_case(case_id)
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE evaluation_cases SET {assignments} WHERE id = ?",
                [*values.values(), case_id],
            )
        if cursor.rowcount == 0:
            raise EvaluationCaseNotFoundError(case_id)
        return self.get_case(case_id)

    def get_case(self, case_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM evaluation_cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            raise EvaluationCaseNotFoundError(case_id)
        return self._case_row(row)

    def list_cases(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM evaluation_cases WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._case_row(row) for row in rows]

    def clear_case_outputs(self, run_id: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM evaluation_metrics WHERE run_id = ?", (run_id,))
            conn.execute("DELETE FROM evaluation_findings WHERE run_id = ?", (run_id,))

    def add_metric(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "case_id": data.get("case_id"),
            "metric_name": data["metric_name"],
            "metric_value": data.get("metric_value"),
            "metric_unit": data.get("metric_unit"),
            "metric_json": _json(data.get("metric"), {}),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_metrics (
                  id, run_id, case_id, metric_name, metric_value,
                  metric_unit, metric_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return item | {"metric_id": item["id"], "metric": _loads(item["metric_json"], {})}

    def list_metrics(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM evaluation_metrics WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
        return [self._metric_row(row) for row in rows]

    def add_finding(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "case_id": data.get("case_id"),
            "severity": data.get("severity", "info"),
            "category": data["category"],
            "title": data["title"],
            "message": data["message"],
            "evidence_json": _json(data.get("evidence"), {}),
            "suggestion": data.get("suggestion"),
            "status": data.get("status", "open"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_findings (
                  id, run_id, case_id, severity, category, title, message,
                  evidence_json, suggestion, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_finding(item["id"])

    def get_finding(self, finding_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evaluation_findings WHERE id = ?",
                (finding_id,),
            ).fetchone()
        if row is None:
            raise EvaluationFindingNotFoundError(finding_id)
        return self._finding_row(row)

    def update_finding_status(self, finding_id: str, status: str) -> dict[str, Any]:
        self.get_finding(finding_id)
        now = _now()
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                "UPDATE evaluation_findings SET status = ?, updated_at = ? WHERE id = ?",
                (status, now, finding_id),
            )
        if cursor.rowcount == 0:
            raise EvaluationFindingNotFoundError(finding_id)
        return self.get_finding(finding_id)

    def list_findings(
        self,
        run_id: str,
        *,
        category: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self.get_run(run_id)
        clauses = ["run_id = ?"]
        params: list[Any] = [run_id]
        for field, value in (
            ("category", category),
            ("severity", severity),
            ("status", status),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM evaluation_findings WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at ASC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._finding_row(row) for row in rows]

    def add_manual_score(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "target_type": data["target_type"],
            "target_id": data["target_id"],
            "reviewer_id": data.get("reviewer_id"),
            "overall_score": data.get("overall_score"),
            "dimensions_json": _json(data.get("dimensions"), {}),
            "notes": data.get("notes"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO manual_evaluation_scores (
                  id, run_id, target_type, target_id, reviewer_id,
                  overall_score, dimensions_json, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self._manual_row_from_item(item)

    def list_manual_scores(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM manual_evaluation_scores WHERE run_id = ? ORDER BY created_at DESC",
                (run_id,),
            ).fetchall()
        return [self._manual_row(row) for row in rows]

    def create_report(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "report_type": data.get("report_type", "summary"),
            "report_json": _json(data.get("report"), {}),
            "summary_text": data.get("summary_text"),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO evaluation_reports (
                  id, run_id, report_type, report_json, summary_text, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_report(item["id"])

    def get_report(self, report_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM evaluation_reports WHERE id = ?",
                (report_id,),
            ).fetchone()
        if row is None:
            raise EvaluationReportNotFoundError(report_id)
        return self._report_row(row)

    def list_reports(self, run_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM evaluation_reports
                WHERE run_id = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (run_id, max(1, min(limit, 200)), max(0, offset)),
            ).fetchall()
        return [self._report_row(row) for row in rows]

    @staticmethod
    def _run_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["run_id"] = data.pop("id")
        data["evaluator_config"] = _loads(data.pop("evaluator_config_json"), {})
        return data

    @staticmethod
    def _case_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["case_id"] = data.pop("id")
        data["input_snapshot"] = _loads(data.pop("input_snapshot_json"), {})
        return data

    @staticmethod
    def _metric_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metric_id"] = data.pop("id")
        data["metric"] = _loads(data.pop("metric_json"), {})
        return data

    @staticmethod
    def _finding_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["finding_id"] = data.pop("id")
        data["evidence"] = _loads(data.pop("evidence_json"), {})
        return data

    @staticmethod
    def _manual_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["manual_score_id"] = data.pop("id")
        data["dimensions"] = _loads(data.pop("dimensions_json"), {})
        return data

    @staticmethod
    def _manual_row_from_item(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "manual_score_id": item["id"],
            "run_id": item["run_id"],
            "target_type": item["target_type"],
            "target_id": item["target_id"],
            "reviewer_id": item.get("reviewer_id"),
            "overall_score": item.get("overall_score"),
            "dimensions": _loads(item["dimensions_json"], {}),
            "notes": item.get("notes"),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }

    @staticmethod
    def _report_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["report_id"] = data.pop("id")
        data["report"] = _loads(data.pop("report_json"), {})
        return data
