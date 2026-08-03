"""SQLite migrations for Novel Studio Stage 10 Memory / RAG."""

from __future__ import annotations

import sqlite3
from pathlib import Path

MEMORY_TABLES = (
    "memory_documents",
    "memory_chunks",
    "memory_index_entries",
    "memory_retrieval_records",
    "chapter_summary_versions",
)


def initialize_memory_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_documents (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              source_type TEXT NOT NULL,
              source_id TEXT NOT NULL,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              summary TEXT,
              tags_json TEXT NOT NULL DEFAULT '[]',
              priority INTEGER NOT NULL DEFAULT 0,
              status TEXT NOT NULL DEFAULT 'active',
              content_hash TEXT NOT NULL,
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_documents_project
            ON memory_documents(project_id, source_type, status, updated_at)
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_documents_source
            ON memory_documents(project_id, source_type, source_id)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_chunks (
              id TEXT PRIMARY KEY,
              document_id TEXT NOT NULL,
              project_id TEXT NOT NULL,
              chunk_index INTEGER NOT NULL,
              chunk_text TEXT NOT NULL,
              chunk_summary TEXT,
              token_estimate INTEGER NOT NULL DEFAULT 0,
              char_count INTEGER NOT NULL DEFAULT 0,
              content_hash TEXT NOT NULL,
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              FOREIGN KEY(document_id) REFERENCES memory_documents(id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_chunks_project
            ON memory_chunks(project_id, document_id, chunk_index)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_index_entries (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chunk_id TEXT NOT NULL,
              index_type TEXT NOT NULL,
              keywords_json TEXT NOT NULL DEFAULT '[]',
              embedding_ref TEXT,
              score_boost REAL NOT NULL DEFAULT 1.0,
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              FOREIGN KEY(chunk_id) REFERENCES memory_chunks(id)
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_index_project
            ON memory_index_entries(project_id, index_type, created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memory_retrieval_records (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chapter_id TEXT,
              scene_id TEXT,
              query_text TEXT NOT NULL,
              mode TEXT NOT NULL,
              top_k INTEGER NOT NULL,
              budget_json TEXT NOT NULL DEFAULT '{}',
              retrieved_chunks_json TEXT NOT NULL DEFAULT '[]',
              selected_chunks_json TEXT NOT NULL DEFAULT '[]',
              warnings_json TEXT NOT NULL DEFAULT '[]',
              total_token_estimate INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_memory_retrieval_project
            ON memory_retrieval_records(project_id, chapter_id, created_at)
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chapter_summary_versions (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              chapter_id TEXT NOT NULL,
              summary_type TEXT NOT NULL DEFAULT 'short',
              summary_text TEXT NOT NULL,
              source_text_hash TEXT NOT NULL,
              generated_by TEXT NOT NULL DEFAULT 'manual',
              model_id TEXT,
              prompt_template_id TEXT,
              status TEXT NOT NULL DEFAULT 'active',
              created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_chapter_summary_versions_chapter
            ON chapter_summary_versions(chapter_id, summary_type, created_at)
            """
        )
        try:
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_chunks_fts
                USING fts5(chunk_id, project_id, title, chunk_text, tokenize='unicode61')
                """
            )
        except sqlite3.OperationalError:
            # SQLite builds without FTS5 are supported through keyword fallback.
            pass


def has_fts5(db_path: str | Path) -> bool:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(path) as conn:
            conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS temp.memory_fts_probe USING fts5(text)")
            conn.execute("DROP TABLE IF EXISTS temp.memory_fts_probe")
        return True
    except sqlite3.OperationalError:
        return False

