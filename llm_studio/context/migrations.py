"""SQLite migration for Context Assembler records."""

from __future__ import annotations

import sqlite3
from pathlib import Path

CONTEXT_TABLES = ("context_assembly_records",)


def initialize_context_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS context_assembly_records (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chapter_id TEXT,
              scene_id TEXT,
              template_id TEXT,
              template_version_id TEXT,
              mode TEXT NOT NULL,
              budget_json TEXT NOT NULL DEFAULT '{}',
              variables_json TEXT NOT NULL DEFAULT '{}',
              selected_items_json TEXT NOT NULL DEFAULT '{}',
              warnings_json TEXT NOT NULL DEFAULT '[]',
              estimated_tokens INTEGER NOT NULL DEFAULT 0,
              estimated_chars INTEGER NOT NULL DEFAULT 0,
              context_hash TEXT NOT NULL,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_context_records_project
            ON context_assembly_records(project_id, chapter_id, created_at)
            """
        )
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(context_assembly_records)").fetchall()
        }
        if "retrieval_id" not in columns:
            conn.execute("ALTER TABLE context_assembly_records ADD COLUMN retrieval_id TEXT")
