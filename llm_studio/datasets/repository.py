"""SQLite persistence for Stage 6 Dataset Builder records."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    DatasetExportNotFoundError,
    DatasetNotFoundError,
    DatasetSampleDuplicateError,
    DatasetSampleNotFoundError,
)
from .migrations import initialize_dataset_database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class DatasetRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_dataset_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create_dataset(self, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "name": data["name"],
            "type": data.get("type", "sft"),
            "description": data.get("description"),
            "project_id": data.get("project_id"),
            "status": data.get("status", "draft"),
            "sample_count": 0,
            "approved_sample_count": 0,
            "rejected_sample_count": 0,
            "metadata_json": json.dumps(data.get("metadata") or {}, ensure_ascii=False, sort_keys=True),
            "created_by": data.get("created_by"),
            "created_at": now,
            "updated_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO training_datasets (
                    id, name, type, description, project_id, status,
                    sample_count, approved_sample_count, rejected_sample_count,
                    metadata_json, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_dataset(item["id"])

    def list_datasets(
        self,
        *,
        project_id: str | None = None,
        type: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        for field, value in (
            ("project_id", project_id),
            ("type", type),
            ("status", status),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        params.extend([max(1, min(limit, 200)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM training_datasets{where} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._dataset_row(row) for row in rows]

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM training_datasets WHERE id = ?",
                (dataset_id,),
            ).fetchone()
        if row is None:
            raise DatasetNotFoundError(dataset_id)
        return self._dataset_row(row)

    def update_dataset(self, dataset_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        allowed_keys = {"name", "type", "description", "project_id", "status", "metadata_json"}
        values = {key: value for key, value in changes.items() if key in allowed_keys}
        if not values:
            return self.get_dataset(dataset_id)
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE training_datasets SET {assignments} WHERE id = ?",
                [*values.values(), dataset_id],
            )
        if cursor.rowcount == 0:
            raise DatasetNotFoundError(dataset_id)
        return self.get_dataset(dataset_id)

    def refresh_dataset_counts(self, dataset_id: str) -> dict[str, Any]:
        with self._lock, self._connect() as conn:
            exists = conn.execute(
                "SELECT id FROM training_datasets WHERE id = ?",
                (dataset_id,),
            ).fetchone()
            if exists is None:
                raise DatasetNotFoundError(dataset_id)
            counts = conn.execute(
                """
                SELECT
                  SUM(CASE WHEN status != 'archived' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END)
                FROM training_samples
                WHERE dataset_id = ?
                """,
                (dataset_id,),
            ).fetchone()
            conn.execute(
                """
                UPDATE training_datasets
                SET sample_count = ?, approved_sample_count = ?,
                    rejected_sample_count = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    int(counts[0] or 0),
                    int(counts[1] or 0),
                    int(counts[2] or 0),
                    _now(),
                    dataset_id,
                ),
            )
        return self.get_dataset(dataset_id)

    def create_sample(self, dataset_id: str, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "dataset_id": dataset_id,
            "project_id": data.get("project_id"),
            "chapter_id": data.get("chapter_id"),
            "revision_id": data.get("revision_id"),
            "generation_id": data.get("generation_id"),
            "sample_type": data.get("sample_type", "sft"),
            "instruction": data["instruction"],
            "input": data.get("input") or "",
            "output": data.get("output") or "",
            "chosen": data.get("chosen"),
            "rejected": data.get("rejected"),
            "metadata_json": json.dumps(data.get("metadata") or {}, ensure_ascii=False, sort_keys=True),
            "source_hash": data["source_hash"],
            "content_hash": data["content_hash"],
            "quality_score": data.get("quality_score"),
            "status": data.get("status", "pending"),
            "review_notes": data.get("review_notes"),
            "created_at": now,
            "updated_at": now,
        }
        try:
            with self._lock, self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO training_samples (
                        id, dataset_id, project_id, chapter_id, revision_id,
                        generation_id, sample_type, instruction, input, output,
                        chosen, rejected, metadata_json, source_hash, content_hash,
                        quality_score, status, review_notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tuple(item.values()),
                )
        except sqlite3.IntegrityError as exc:
            if "idx_training_samples_dataset_content_hash" in str(exc) or "UNIQUE" in str(exc):
                raise DatasetSampleDuplicateError("Training sample already exists in this dataset.") from exc
            raise
        self.refresh_dataset_counts(dataset_id)
        return self.get_sample(item["id"])

    def list_samples(
        self,
        dataset_id: str,
        *,
        status: str | None = None,
        sample_type: str | None = None,
        revision_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        self.get_dataset(dataset_id)
        clauses = ["dataset_id = ?"]
        params: list[Any] = [dataset_id]
        for field, value in (
            ("status", status),
            ("sample_type", sample_type),
            ("revision_id", revision_id),
        ):
            if value:
                clauses.append(f"{field} = ?")
                params.append(value)
        params.extend([max(1, min(limit, 500)), max(0, offset)])
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM training_samples WHERE {' AND '.join(clauses)} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                params,
            ).fetchall()
        return [self._sample_row(row) for row in rows]

    def list_samples_for_export(
        self,
        dataset_id: str,
        *,
        approved_only: bool = True,
    ) -> list[dict[str, Any]]:
        self.get_dataset(dataset_id)
        if approved_only:
            query = """
                SELECT * FROM training_samples
                WHERE dataset_id = ? AND status = 'approved'
                ORDER BY created_at ASC
            """
            params = (dataset_id,)
        else:
            query = """
                SELECT * FROM training_samples
                WHERE dataset_id = ? AND status NOT IN ('rejected', 'archived')
                ORDER BY created_at ASC
            """
            params = (dataset_id,)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._sample_row(row) for row in rows]

    def get_sample(self, sample_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM training_samples WHERE id = ?",
                (sample_id,),
            ).fetchone()
        if row is None:
            raise DatasetSampleNotFoundError(sample_id)
        return self._sample_row(row)

    def update_sample(self, sample_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        current = self.get_sample(sample_id)
        allowed_keys = {
            "instruction",
            "input",
            "output",
            "chosen",
            "rejected",
            "metadata_json",
            "content_hash",
            "quality_score",
            "status",
            "review_notes",
        }
        values = {key: value for key, value in changes.items() if key in allowed_keys}
        if not values:
            return current
        values["updated_at"] = _now()
        assignments = ", ".join(f"{key} = ?" for key in values)
        try:
            with self._lock, self._connect() as conn:
                cursor = conn.execute(
                    f"UPDATE training_samples SET {assignments} WHERE id = ?",
                    [*values.values(), sample_id],
                )
        except sqlite3.IntegrityError as exc:
            if "idx_training_samples_dataset_content_hash" in str(exc) or "UNIQUE" in str(exc):
                raise DatasetSampleDuplicateError("Training sample already exists in this dataset.") from exc
            raise
        if cursor.rowcount == 0:
            raise DatasetSampleNotFoundError(sample_id)
        self.refresh_dataset_counts(current["dataset_id"])
        return self.get_sample(sample_id)

    def create_export(self, dataset_id: str, data: dict[str, Any]) -> dict[str, Any]:
        now = _now()
        item = {
            "id": str(uuid.uuid4()),
            "dataset_id": dataset_id,
            "export_format": data["export_format"],
            "export_path": data["export_path"],
            "sample_count": int(data.get("sample_count") or 0),
            "approved_only": 1 if data.get("approved_only", True) else 0,
            "export_hash": data.get("export_hash"),
            "status": data.get("status", "created"),
            "created_at": now,
        }
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dataset_exports (
                    id, dataset_id, export_format, export_path, sample_count,
                    approved_only, export_hash, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                tuple(item.values()),
            )
        return self.get_export(item["id"])

    def list_exports(self, dataset_id: str, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        self.get_dataset(dataset_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dataset_exports
                WHERE dataset_id = ?
                ORDER BY created_at DESC LIMIT ? OFFSET ?
                """,
                (dataset_id, max(1, min(limit, 200)), max(0, offset)),
            ).fetchall()
        return [self._export_row(row) for row in rows]

    def get_export(self, export_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM dataset_exports WHERE id = ?",
                (export_id,),
            ).fetchone()
        if row is None:
            raise DatasetExportNotFoundError(export_id)
        return self._export_row(row)

    @staticmethod
    def _dataset_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["dataset_id"] = data.pop("id")
        data["metadata"] = _loads(data.pop("metadata_json"), {})
        return data

    @staticmethod
    def _sample_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["sample_id"] = data.pop("id")
        data["metadata"] = _loads(data.pop("metadata_json"), {})
        data["warnings"] = data["metadata"].get("warnings", [])
        return data

    @staticmethod
    def _export_row(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["export_id"] = data.pop("id")
        data["format"] = data["export_format"]
        data["approved_only"] = bool(data["approved_only"])
        return data
