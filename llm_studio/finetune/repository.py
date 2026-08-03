"""SQLite persistence for Novel Studio Fine-tune Center records."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import FineTuneCheckpointNotFoundError, FineTuneRunNotFoundError
from .migrations import initialize_finetune_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class FineTuneRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_finetune_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_run(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "job_id": data.get("job_id"),
            "dataset_version_id": data["dataset_version_id"],
            "recipe_id": data["recipe_id"],
            "base_model_id": data["base_model_id"],
            "method": data["method"],
            "adapter_name": data["adapter_name"],
            "adapter_id": data.get("adapter_id"),
            "status": data.get("status", "created"),
            "config_snapshot_json": json.dumps(
                data.get("config_snapshot") or {},
                ensure_ascii=False,
                sort_keys=True,
            ),
            "dataset_manifest_snapshot_json": json.dumps(
                data.get("dataset_manifest_snapshot") or {},
                ensure_ascii=False,
                sort_keys=True,
            ),
            "current_step": int(data.get("current_step") or 0),
            "total_steps": int(data.get("total_steps") or 0),
            "current_epoch": data.get("current_epoch"),
            "train_loss": data.get("train_loss"),
            "val_loss": data.get("val_loss"),
            "best_val_loss": data.get("best_val_loss"),
            "best_step": data.get("best_step"),
            "best_checkpoint_id": data.get("best_checkpoint_id"),
            "last_checkpoint_id": data.get("last_checkpoint_id"),
            "output_adapter_path": data.get("output_adapter_path"),
            "metrics_path": data.get("metrics_path"),
            "log_path": data.get("log_path"),
            "error_code": data.get("error_code"),
            "error_message": data.get("error_message"),
            "cancel_requested": 1 if data.get("cancel_requested") else 0,
            "resume_from_checkpoint_id": data.get("resume_from_checkpoint_id"),
            "started_at": data.get("started_at"),
            "finished_at": data.get("finished_at"),
            "created_at": data.get("created_at") or now,
            "updated_at": data.get("updated_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO finetune_runs (
                    id, job_id, dataset_version_id, recipe_id, base_model_id,
                    method, adapter_name, adapter_id, status,
                    config_snapshot_json, dataset_manifest_snapshot_json,
                    current_step, total_steps, current_epoch, train_loss,
                    val_loss, best_val_loss, best_step, best_checkpoint_id,
                    last_checkpoint_id, output_adapter_path, metrics_path,
                    log_path, error_code, error_message, cancel_requested,
                    resume_from_checkpoint_id, started_at, finished_at,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_run(item["id"])

    def update_run(self, run_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get_run(run_id)
        allowed = {
            "job_id",
            "adapter_id",
            "status",
            "config_snapshot_json",
            "dataset_manifest_snapshot_json",
            "current_step",
            "total_steps",
            "current_epoch",
            "train_loss",
            "val_loss",
            "best_val_loss",
            "best_step",
            "best_checkpoint_id",
            "last_checkpoint_id",
            "output_adapter_path",
            "metrics_path",
            "log_path",
            "error_code",
            "error_message",
            "cancel_requested",
            "resume_from_checkpoint_id",
            "started_at",
            "finished_at",
        }
        values = {key: value for key, value in changes.items() if key in allowed}
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE finetune_runs SET {assignments} WHERE id = ?",
                [*values.values(), run_id],
            )
        if cursor.rowcount == 0:
            raise FineTuneRunNotFoundError(run_id)
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM finetune_runs WHERE id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise FineTuneRunNotFoundError(run_id)
        return self._run_row(row)

    def list_runs(
        self,
        *,
        status: str | None = None,
        dataset_version_id: str | None = None,
        base_model_id: str | None = None,
        method: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("status", status),
            ("dataset_version_id", dataset_version_id),
            ("base_model_id", base_model_id),
            ("method", method),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM finetune_runs{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._run_row(row) for row in rows]

    def create_checkpoint(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "checkpoint_type": data["checkpoint_type"],
            "step": int(data["step"]),
            "epoch": data.get("epoch"),
            "train_loss": data.get("train_loss"),
            "val_loss": data.get("val_loss"),
            "checkpoint_path": data["checkpoint_path"],
            "checkpoint_hash": data.get("checkpoint_hash"),
            "size_bytes": data.get("size_bytes"),
            "is_best": 1 if data.get("is_best") else 0,
            "is_last": 1 if data.get("is_last") else 0,
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            if item["is_best"]:
                conn.execute("UPDATE finetune_checkpoints SET is_best = 0 WHERE run_id = ?", (item["run_id"],))
            if item["is_last"]:
                conn.execute("UPDATE finetune_checkpoints SET is_last = 0 WHERE run_id = ?", (item["run_id"],))
            conn.execute(
                """
                INSERT INTO finetune_checkpoints (
                    id, run_id, checkpoint_type, step, epoch, train_loss,
                    val_loss, checkpoint_path, checkpoint_hash, size_bytes,
                    is_best, is_last, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_checkpoint(item["id"])

    def get_checkpoint(self, checkpoint_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM finetune_checkpoints WHERE id = ?",
                (checkpoint_id,),
            ).fetchone()
        if row is None:
            raise FineTuneCheckpointNotFoundError(checkpoint_id)
        return self._checkpoint_row(row)

    def list_checkpoints(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM finetune_checkpoints
                WHERE run_id = ?
                ORDER BY step DESC, created_at DESC
                """,
                (run_id,),
            ).fetchall()
        return [self._checkpoint_row(row) for row in rows]

    def create_metric(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "step": int(data["step"]),
            "epoch": data.get("epoch"),
            "metric_type": data["metric_type"],
            "metrics_json": json.dumps(
                data.get("metrics") or {},
                ensure_ascii=False,
                sort_keys=True,
            ),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO finetune_metrics (
                    id, run_id, step, epoch, metric_type, metrics_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return item | {
            "metric_id": item["id"],
            "metrics": _loads(item["metrics_json"], {}),
        }

    def list_metrics(self, run_id: str, *, limit: int = 500, offset: int = 0) -> list[dict[str, Any]]:
        self.get_run(run_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM finetune_metrics
                WHERE run_id = ?
                ORDER BY step ASC, created_at ASC LIMIT ? OFFSET ?
                """,
                (run_id, max(1, min(limit, 2000)), max(0, offset)),
            ).fetchall()
        return [self._metric_row(row) for row in rows]

    def create_log(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": data.get("id") or str(uuid.uuid4()),
            "run_id": data["run_id"],
            "level": data.get("level", "info"),
            "message": data["message"],
            "event_type": data.get("event_type"),
            "step": data.get("step"),
            "created_at": data.get("created_at") or now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO finetune_logs (
                    id, run_id, level, message, event_type, step, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return item | {"log_id": item["id"]}

    def list_logs(
        self,
        run_id: str,
        *,
        level: str | None = None,
        since: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self.get_run(run_id)
        clauses = ["run_id = ?"]
        params: list[Any] = [run_id]
        if level:
            clauses.append("level = ?")
            params.append(level)
        if since:
            clauses.append("created_at >= ?")
            params.append(since)
        params.extend([max(1, min(limit, 1000)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM finetune_logs WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at ASC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._log_row(row) for row in rows]

    @staticmethod
    def _run_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["run_id"] = data.pop("id")
        data["config_snapshot"] = _loads(data.pop("config_snapshot_json"), {})
        data["dataset_manifest_snapshot"] = _loads(
            data.pop("dataset_manifest_snapshot_json"),
            {},
        )
        data["cancel_requested"] = bool(data["cancel_requested"])
        return data

    @staticmethod
    def _checkpoint_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["checkpoint_id"] = data.pop("id")
        data["is_best"] = bool(data["is_best"])
        data["is_last"] = bool(data["is_last"])
        return data

    @staticmethod
    def _metric_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["metric_id"] = data.pop("id")
        data["metrics"] = _loads(data.pop("metrics_json"), {})
        return data

    @staticmethod
    def _log_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["log_id"] = data.pop("id")
        return data
