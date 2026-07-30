"""SQLite migrations for Novel Studio stage 1."""

from __future__ import annotations

import sqlite3
from pathlib import Path

NOVEL_TABLES = (
    "novel_projects",
    "novel_volumes",
    "novel_chapters",
    "novel_scenes",
    "novel_characters",
    "novel_world_entries",
    "novel_plot_threads",
    "novel_timeline_events",
)


def initialize_novel_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS novel_projects (
              id TEXT PRIMARY KEY,
              title TEXT NOT NULL,
              slug TEXT NOT NULL UNIQUE,
              genre TEXT,
              description TEXT,
              target_style TEXT,
              target_audience TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS novel_volumes (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              title TEXT NOT NULL,
              volume_index INTEGER NOT NULL,
              outline TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id)
            );
            CREATE INDEX IF NOT EXISTS idx_novel_volumes_project
            ON novel_volumes(project_id, volume_index);

            CREATE TABLE IF NOT EXISTS novel_chapters (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              volume_id TEXT,
              title TEXT NOT NULL,
              chapter_index INTEGER NOT NULL,
              outline TEXT,
              draft_content TEXT,
              final_content TEXT,
              summary TEXT,
              word_count INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'outline',
              version INTEGER NOT NULL DEFAULT 1,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id),
              FOREIGN KEY(volume_id) REFERENCES novel_volumes(id)
            );
            CREATE INDEX IF NOT EXISTS idx_novel_chapters_project
            ON novel_chapters(project_id, chapter_index);

            CREATE TABLE IF NOT EXISTS novel_scenes (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chapter_id TEXT NOT NULL,
              title TEXT NOT NULL,
              scene_index INTEGER NOT NULL,
              outline TEXT,
              content TEXT,
              pov_character_id TEXT,
              location TEXT,
              timeline_note TEXT,
              status TEXT NOT NULL DEFAULT 'outline',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id),
              FOREIGN KEY(chapter_id) REFERENCES novel_chapters(id)
            );

            CREATE TABLE IF NOT EXISTS novel_characters (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              name TEXT NOT NULL,
              aliases TEXT,
              role TEXT,
              personality TEXT,
              background TEXT,
              goals TEXT,
              relationships TEXT,
              speech_style TEXT,
              appearance TEXT,
              notes TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id)
            );

            CREATE TABLE IF NOT EXISTS novel_world_entries (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              category TEXT NOT NULL,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              tags TEXT,
              priority INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id)
            );

            CREATE TABLE IF NOT EXISTS novel_plot_threads (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT,
              status TEXT NOT NULL DEFAULT 'open',
              priority INTEGER NOT NULL DEFAULT 0,
              related_character_ids TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id)
            );

            CREATE TABLE IF NOT EXISTS novel_timeline_events (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              title TEXT NOT NULL,
              event_order INTEGER NOT NULL,
              chapter_id TEXT,
              scene_id TEXT,
              description TEXT,
              involved_character_ids TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(project_id) REFERENCES novel_projects(id)
            );
            """
        )
