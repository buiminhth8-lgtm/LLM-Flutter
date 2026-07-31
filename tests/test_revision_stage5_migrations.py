import sqlite3

from llm_studio.revisions.migrations import REVISION_TABLES, initialize_revision_database


def test_revision_tables_are_idempotent(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_revision_database(db_path)
    initialize_revision_database(db_path)

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

    assert set(REVISION_TABLES).issubset(tables)
    assert "idx_revision_records_project" in indexes
    assert "idx_revision_records_chapter" in indexes
    assert "idx_revision_records_generation" in indexes
