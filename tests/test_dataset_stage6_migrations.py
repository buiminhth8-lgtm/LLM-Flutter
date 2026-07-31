from __future__ import annotations

import sqlite3

from llm_studio.datasets.migrations import initialize_dataset_database


def test_dataset_stage6_tables_are_idempotent(tmp_path):
    db_path = tmp_path / "novels.sqlite"

    initialize_dataset_database(db_path)
    initialize_dataset_database(db_path)

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

    assert "training_datasets" in tables
    assert "training_samples" in tables
    assert "dataset_exports" in tables
    assert "idx_training_samples_dataset" in indexes
    assert "idx_training_samples_revision" in indexes
    assert "idx_training_samples_dataset_content_hash" in indexes
    assert "dataset_versions" in tables
    assert "finetune_runs" not in tables
