"""SQLite migrations for Novel Studio Stage 8 Fine-tune Center."""

from __future__ import annotations

import sqlite3
from pathlib import Path

FINETUNE_TABLES = (
    "finetune_runs",
    "finetune_checkpoints",
    "finetune_metrics",
    "finetune_logs",
)


def initialize_finetune_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finetune_runs (
              id TEXT PRIMARY KEY,
              job_id TEXT,
              dataset_version_id TEXT NOT NULL,
              recipe_id TEXT NOT NULL,
              base_model_id TEXT NOT NULL,
              method TEXT NOT NULL,
              adapter_name TEXT NOT NULL,
              adapter_id TEXT,
              status TEXT NOT NULL DEFAULT 'created',
              config_snapshot_json TEXT NOT NULL DEFAULT '{}',
              dataset_manifest_snapshot_json TEXT NOT NULL DEFAULT '{}',
              current_step INTEGER NOT NULL DEFAULT 0,
              total_steps INTEGER NOT NULL DEFAULT 0,
              current_epoch REAL,
              train_loss REAL,
              val_loss REAL,
              best_val_loss REAL,
              best_step INTEGER,
              best_checkpoint_id TEXT,
              last_checkpoint_id TEXT,
              output_adapter_path TEXT,
              metrics_path TEXT,
              log_path TEXT,
              error_code TEXT,
              error_message TEXT,
              cancel_requested INTEGER NOT NULL DEFAULT 0,
              resume_from_checkpoint_id TEXT,
              started_at TEXT,
              finished_at TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finetune_checkpoints (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              checkpoint_type TEXT NOT NULL,
              step INTEGER NOT NULL,
              epoch REAL,
              train_loss REAL,
              val_loss REAL,
              checkpoint_path TEXT NOT NULL,
              checkpoint_hash TEXT,
              size_bytes INTEGER,
              is_best INTEGER NOT NULL DEFAULT 0,
              is_last INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES finetune_runs(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finetune_metrics (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              step INTEGER NOT NULL,
              epoch REAL,
              metric_type TEXT NOT NULL,
              metrics_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES finetune_runs(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS finetune_logs (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              level TEXT NOT NULL DEFAULT 'info',
              message TEXT NOT NULL,
              event_type TEXT,
              step INTEGER,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES finetune_runs(id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_runs_dataset_version
            ON finetune_runs(dataset_version_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_runs_job
            ON finetune_runs(job_id);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_runs_status
            ON finetune_runs(status, updated_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_checkpoints_run
            ON finetune_checkpoints(run_id, step);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_metrics_run
            ON finetune_metrics(run_id, metric_type, step);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_finetune_logs_run
            ON finetune_logs(run_id, created_at);
            """
        )
