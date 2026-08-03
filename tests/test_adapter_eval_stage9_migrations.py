from __future__ import annotations

import sqlite3

from llm_studio.adapter_evaluation.migrations import (
    ADAPTER_EVALUATION_TABLES,
    initialize_adapter_evaluation_database,
)


def test_adapter_eval_stage9_tables_initialize(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_adapter_evaluation_database(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }
    assert set(ADAPTER_EVALUATION_TABLES).issubset(tables)
    assert "idx_adapter_eval_results_case_variant" in indexes
    assert "idx_adapter_eval_scores_case" in indexes
