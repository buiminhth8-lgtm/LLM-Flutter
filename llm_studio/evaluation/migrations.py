"""SQLite migrations for Stage 11 Evaluation Center."""

from __future__ import annotations

import sqlite3
from pathlib import Path

EVALUATION_TABLES = (
    "evaluation_runs",
    "evaluation_cases",
    "evaluation_metrics",
    "evaluation_findings",
    "evaluation_reports",
    "manual_evaluation_scores",
)


def initialize_evaluation_database(db_path: str | Path) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_runs (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT,
              project_id TEXT,
              chapter_id TEXT,
              generation_id TEXT,
              revision_id TEXT,
              adapter_eval_session_id TEXT,
              memory_retrieval_id TEXT,
              target_type TEXT NOT NULL,
              target_id TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'created',
              evaluator_config_json TEXT NOT NULL DEFAULT '{}',
              overall_score REAL,
              summary_text TEXT,
              error_code TEXT,
              error_message TEXT,
              job_id TEXT,
              created_by TEXT,
              started_at TEXT,
              finished_at TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_runs_target "
            "ON evaluation_runs(target_type, target_id, created_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_runs_project "
            "ON evaluation_runs(project_id, status, created_at)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_cases (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              project_id TEXT,
              chapter_id TEXT,
              target_type TEXT NOT NULL,
              target_id TEXT NOT NULL,
              evaluator_type TEXT NOT NULL,
              input_snapshot_json TEXT NOT NULL DEFAULT '{}',
              status TEXT NOT NULL DEFAULT 'pending',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES evaluation_runs(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_cases_run "
            "ON evaluation_cases(run_id, evaluator_type)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              case_id TEXT,
              metric_name TEXT NOT NULL,
              metric_value REAL,
              metric_unit TEXT,
              metric_json TEXT NOT NULL DEFAULT '{}',
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES evaluation_runs(id),
              FOREIGN KEY(case_id) REFERENCES evaluation_cases(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_metrics_run "
            "ON evaluation_metrics(run_id, metric_name)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_findings (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              case_id TEXT,
              severity TEXT NOT NULL DEFAULT 'info',
              category TEXT NOT NULL,
              title TEXT NOT NULL,
              message TEXT NOT NULL,
              evidence_json TEXT NOT NULL DEFAULT '{}',
              suggestion TEXT,
              status TEXT NOT NULL DEFAULT 'open',
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES evaluation_runs(id),
              FOREIGN KEY(case_id) REFERENCES evaluation_cases(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_findings_run "
            "ON evaluation_findings(run_id, severity, category, status)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS evaluation_reports (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              report_type TEXT NOT NULL DEFAULT 'summary',
              report_json TEXT NOT NULL DEFAULT '{}',
              summary_text TEXT,
              created_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES evaluation_runs(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_evaluation_reports_run "
            "ON evaluation_reports(run_id, created_at)"
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS manual_evaluation_scores (
              id TEXT PRIMARY KEY,
              run_id TEXT NOT NULL,
              target_type TEXT NOT NULL,
              target_id TEXT NOT NULL,
              reviewer_id TEXT,
              overall_score INTEGER,
              dimensions_json TEXT NOT NULL DEFAULT '{}',
              notes TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              FOREIGN KEY(run_id) REFERENCES evaluation_runs(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_manual_evaluation_scores_run "
            "ON manual_evaluation_scores(run_id, created_at)"
        )
