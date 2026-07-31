"""SQLite schema initialization for Novel Studio Stage 4."""

from __future__ import annotations

import sqlite3
from pathlib import Path

WRITING_TABLES = ("generation_records",)


def initialize_writing_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS generation_records (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chapter_id TEXT,
              scene_id TEXT,
              template_id TEXT,
              template_version_id TEXT,
              context_id TEXT,
              model_id TEXT NOT NULL,
              adapter_id TEXT,
              mode TEXT NOT NULL,
              prompt_rendered TEXT NOT NULL,
              input_context_json TEXT NOT NULL DEFAULT '{}',
              model_output TEXT NOT NULL DEFAULT '',
              generation_params_json TEXT NOT NULL DEFAULT '{}',
              target_length_json TEXT NOT NULL DEFAULT '{}',
              status TEXT NOT NULL DEFAULT 'created',
              finish_reason TEXT,
              prompt_hash TEXT,
              context_hash TEXT,
              output_hash TEXT,
              input_token_estimate INTEGER NOT NULL DEFAULT 0,
              output_token_estimate INTEGER NOT NULL DEFAULT 0,
              output_char_count INTEGER NOT NULL DEFAULT 0,
              latency_ms INTEGER,
              error_code TEXT,
              error_message TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_generation_records_project
            ON generation_records(project_id, created_at);

            CREATE INDEX IF NOT EXISTS idx_generation_records_chapter
            ON generation_records(chapter_id, created_at);
            """
        )
