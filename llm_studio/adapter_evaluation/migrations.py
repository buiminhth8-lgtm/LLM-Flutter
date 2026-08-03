"""SQLite migrations for Novel Studio Stage 9 Adapter Evaluation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ADAPTER_EVALUATION_TABLES = (
    "adapter_evaluation_sessions",
    "adapter_evaluation_cases",
    "adapter_evaluation_results",
    "adapter_evaluation_scores",
    "adapter_evaluation_reports",
)


def initialize_adapter_evaluation_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS adapter_evaluation_sessions (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT,
              project_id TEXT,
              finetune_run_id TEXT,
              dataset_version_id TEXT,
              base_model_id TEXT NOT NULL,
              adapter_id TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'draft',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              created_by TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS adapter_evaluation_cases (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              project_id TEXT,
              chapter_id TEXT,
              scene_id TEXT,
              template_id TEXT,
              template_version_id TEXT,
              context_id TEXT,
              mode TEXT NOT NULL,
              title TEXT NOT NULL,
              user_variables_json TEXT NOT NULL DEFAULT '{}',
              generation_params_json TEXT NOT NULL DEFAULT '{}',
              target_length_json TEXT NOT NULL DEFAULT '{}',
              prompt_rendered TEXT,
              context_snapshot_json TEXT NOT NULL DEFAULT '{}',
              prompt_hash TEXT,
              context_hash TEXT,
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(session_id) REFERENCES adapter_evaluation_sessions(id)
            );
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS adapter_evaluation_results (
              id TEXT PRIMARY KEY,
              case_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              variant TEXT NOT NULL,
              model_id TEXT NOT NULL,
              adapter_id TEXT,
              output_text TEXT NOT NULL DEFAULT '',
              generation_record_id TEXT,
              status TEXT NOT NULL DEFAULT 'created',
              finish_reason TEXT,
              output_hash TEXT,
              output_char_count INTEGER NOT NULL DEFAULT 0,
              output_token_estimate INTEGER NOT NULL DEFAULT 0,
              latency_ms INTEGER,
              error_code TEXT,
              error_message TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES adapter_evaluation_cases(id),
              FOREIGN KEY(session_id) REFERENCES adapter_evaluation_sessions(id)
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_adapter_eval_results_case_variant
            ON adapter_evaluation_results(case_id, variant);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS adapter_evaluation_scores (
              id TEXT PRIMARY KEY,
              case_id TEXT NOT NULL,
              session_id TEXT NOT NULL,
              base_result_id TEXT,
              adapter_result_id TEXT,
              winner TEXT,
              base_score INTEGER,
              adapter_score INTEGER,
              dimensions_json TEXT NOT NULL DEFAULT '{}',
              notes TEXT,
              reviewer_id TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(case_id) REFERENCES adapter_evaluation_cases(id),
              FOREIGN KEY(session_id) REFERENCES adapter_evaluation_sessions(id)
            );
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_adapter_eval_scores_case
            ON adapter_evaluation_scores(case_id);
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS adapter_evaluation_reports (
              id TEXT PRIMARY KEY,
              session_id TEXT NOT NULL,
              report_json TEXT NOT NULL DEFAULT '{}',
              summary_text TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(session_id) REFERENCES adapter_evaluation_sessions(id)
            );
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adapter_eval_sessions_project
            ON adapter_evaluation_sessions(project_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adapter_eval_sessions_adapter
            ON adapter_evaluation_sessions(adapter_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adapter_eval_cases_session
            ON adapter_evaluation_cases(session_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adapter_eval_results_session
            ON adapter_evaluation_results(session_id, created_at);
            """
        )
        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_adapter_eval_reports_session
            ON adapter_evaluation_reports(session_id, created_at);
            """
        )
