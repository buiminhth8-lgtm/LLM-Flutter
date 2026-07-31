"""SQLite migrations for Novel Studio Stage 6 Dataset Builder."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DATASET_TABLES = ("training_datasets", "training_samples", "dataset_exports")


def initialize_dataset_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_datasets (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              type TEXT NOT NULL DEFAULT 'sft',
              description TEXT,
              project_id TEXT,
              status TEXT NOT NULL DEFAULT 'draft',
              sample_count INTEGER NOT NULL DEFAULT 0,
              approved_sample_count INTEGER NOT NULL DEFAULT 0,
              rejected_sample_count INTEGER NOT NULL DEFAULT 0,
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_by TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS training_samples (
              id TEXT PRIMARY KEY,
              dataset_id TEXT NOT NULL,
              project_id TEXT,
              chapter_id TEXT,
              revision_id TEXT,
              generation_id TEXT,
              sample_type TEXT NOT NULL DEFAULT 'sft',
              instruction TEXT NOT NULL,
              input TEXT NOT NULL DEFAULT '',
              output TEXT NOT NULL DEFAULT '',
              chosen TEXT,
              rejected TEXT,
              metadata_json TEXT NOT NULL DEFAULT '{}',
              source_hash TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              quality_score INTEGER,
              status TEXT NOT NULL DEFAULT 'pending',
              review_notes TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(dataset_id) REFERENCES training_datasets(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dataset_exports (
              id TEXT PRIMARY KEY,
              dataset_id TEXT NOT NULL,
              export_format TEXT NOT NULL,
              export_path TEXT NOT NULL,
              sample_count INTEGER NOT NULL DEFAULT 0,
              approved_only INTEGER NOT NULL DEFAULT 1,
              export_hash TEXT,
              status TEXT NOT NULL DEFAULT 'created',
              created_at TEXT NOT NULL,
              FOREIGN KEY(dataset_id) REFERENCES training_datasets(id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_training_datasets_project
            ON training_datasets(project_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_training_samples_dataset
            ON training_samples(dataset_id, status);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_training_samples_revision
            ON training_samples(revision_id);
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_training_samples_dataset_content_hash
            ON training_samples(dataset_id, content_hash);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_dataset_exports_dataset
            ON dataset_exports(dataset_id, created_at);
            """
        )
