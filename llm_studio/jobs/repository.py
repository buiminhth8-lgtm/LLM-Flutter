"""SQLite-backed job repository."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from .entities import Job, JobStatus
from .exceptions import JobNotFoundError


class JobRepository:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._init_db()
        self.mark_running_interrupted()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    error_code TEXT,
                    error_message TEXT,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC)")

    def save(self, job: Job) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO jobs (
                    id, type, status, progress, message, created_at, started_at,
                    finished_at, error_code, error_message, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    type=excluded.type,
                    status=excluded.status,
                    progress=excluded.progress,
                    message=excluded.message,
                    started_at=excluded.started_at,
                    finished_at=excluded.finished_at,
                    error_code=excluded.error_code,
                    error_message=excluded.error_message,
                    payload=excluded.payload
                """,
                (
                    job.id,
                    job.type,
                    job.status,
                    job.progress,
                    job.message,
                    job.created_at.isoformat(),
                    job.started_at.isoformat() if job.started_at else None,
                    job.finished_at.isoformat() if job.finished_at else None,
                    job.error_code,
                    job.error_message,
                    json.dumps(job.payload, ensure_ascii=False),
                ),
            )

    def get(self, job_id: str) -> Job:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            raise JobNotFoundError(job_id)
        return self._row_to_job(row)

    def delete(self, job_id: str) -> bool:
        with self._lock, self._connect() as conn:
            cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cursor.rowcount > 0

    def list(self, *, limit: int = 50, offset: int = 0) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._row_to_job(row) for row in rows]

    def mark_running_interrupted(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, finished_at = ?, error_code = ?, error_message = ?
                WHERE status IN (?, ?)
                """,
                (
                    JobStatus.INTERRUPTED.value,
                    now,
                    "JOB_INTERRUPTED",
                    "应用重启或进程退出时任务未完成。",
                    JobStatus.RUNNING.value,
                    JobStatus.CANCELLING.value,
                ),
            )

    def cleanup(self, *, keep_last: int = 500) -> int:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT id FROM jobs ORDER BY created_at DESC LIMIT -1 OFFSET ?",
                (keep_last,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            if ids:
                conn.executemany("DELETE FROM jobs WHERE id = ?", [(item,) for item in ids])
        return len(ids)

    def _row_to_job(self, row: sqlite3.Row) -> Job:
        return Job.from_dict(
            {
                "id": row["id"],
                "type": row["type"],
                "status": row["status"],
                "progress": row["progress"],
                "message": row["message"],
                "created_at": row["created_at"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "error_code": row["error_code"],
                "error_message": row["error_message"],
                "payload": json.loads(row["payload"] or "{}"),
            }
        )
