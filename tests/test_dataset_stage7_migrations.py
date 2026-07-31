from __future__ import annotations

import sqlite3

from llm_studio.datasets.migrations import initialize_dataset_database


def test_stage7_tables_initialize(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_dataset_database(db_path)
    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        indexes = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            ).fetchall()
        }
    assert "dataset_versions" in tables
    assert "dataset_version_samples" in tables
    assert "dataset_change_marks" in tables
    assert "training_recipes" in tables
    assert "idx_dataset_versions_dataset_version" in indexes
    assert "idx_dataset_version_samples_unique_sample" in indexes
