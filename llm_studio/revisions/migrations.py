"""SQLite schema initialization for Novel Studio Stage 5 revisions."""

from __future__ import annotations

import sqlite3
from pathlib import Path

REVISION_TABLES = ("revision_records", "revision_autosaves")


def initialize_revision_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS revision_records (
              id TEXT PRIMARY KEY,
              generation_id TEXT,
              project_id TEXT NOT NULL,
              chapter_id TEXT,
              scene_id TEXT,
              original_text TEXT NOT NULL,
              edited_text TEXT NOT NULL,
              diff_json TEXT NOT NULL DEFAULT '{}',
              edit_tags_json TEXT NOT NULL DEFAULT '[]',
              user_score INTEGER,
              quality_notes TEXT,
              status TEXT NOT NULL DEFAULT 'draft',
              accepted_for_dataset INTEGER NOT NULL DEFAULT 0,
              reviewer_id TEXT,
              source TEXT NOT NULL DEFAULT 'generation',
              original_hash TEXT NOT NULL,
              edited_hash TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_revision_records_project
            ON revision_records(project_id, created_at);

            CREATE INDEX IF NOT EXISTS idx_revision_records_chapter
            ON revision_records(chapter_id, created_at);

            CREATE INDEX IF NOT EXISTS idx_revision_records_generation
            ON revision_records(generation_id);

            CREATE TABLE IF NOT EXISTS revision_autosaves (
              id TEXT PRIMARY KEY,
              revision_id TEXT,
              project_id TEXT NOT NULL,
              chapter_id TEXT,
              generation_id TEXT,
              draft_text TEXT NOT NULL,
              base_text_hash TEXT,
              draft_hash TEXT NOT NULL,
              client_revision INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL
            );
            """
        )
