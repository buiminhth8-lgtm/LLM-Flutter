from __future__ import annotations

import sqlite3

from llm_studio.finetune.migrations import initialize_finetune_database


def test_stage8_finetune_tables_initialize(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_finetune_database(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        indexes = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
        }
    assert "finetune_runs" in tables
    assert "finetune_checkpoints" in tables
    assert "finetune_metrics" in tables
    assert "finetune_logs" in tables
    assert "idx_finetune_runs_dataset_version" in indexes
    assert "idx_finetune_runs_job" in indexes
    assert "idx_finetune_runs_status" in indexes
