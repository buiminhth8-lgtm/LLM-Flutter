"""SQLite migrations for Prompt Studio."""

from __future__ import annotations

import sqlite3
from pathlib import Path

PROMPT_TABLES = ("prompt_templates", "prompt_template_versions", "prompt_render_records")


def initialize_prompt_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS prompt_templates (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              type TEXT NOT NULL,
              description TEXT,
              scope TEXT NOT NULL DEFAULT 'global',
              project_id TEXT,
              active_version_id TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS prompt_template_versions (
              id TEXT PRIMARY KEY,
              template_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              system_prompt TEXT,
              role_prompt TEXT,
              instruction_template TEXT NOT NULL,
              negative_prompt TEXT,
              output_constraints TEXT,
              variables_schema_json TEXT NOT NULL DEFAULT '{}',
              default_values_json TEXT NOT NULL DEFAULT '{}',
              renderer TEXT NOT NULL DEFAULT 'simple_mustache',
              change_note TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(template_id) REFERENCES prompt_templates(id)
            );
            CREATE INDEX IF NOT EXISTS idx_prompt_versions_template
            ON prompt_template_versions(template_id, version);

            CREATE TABLE IF NOT EXISTS prompt_render_records (
              id TEXT PRIMARY KEY,
              template_id TEXT NOT NULL,
              template_version_id TEXT NOT NULL,
              project_id TEXT,
              chapter_id TEXT,
              variables_json TEXT NOT NULL DEFAULT '{}',
              rendered_prompt TEXT NOT NULL,
              missing_variables_json TEXT NOT NULL DEFAULT '[]',
              warnings_json TEXT NOT NULL DEFAULT '[]',
              prompt_hash TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            """
        )
