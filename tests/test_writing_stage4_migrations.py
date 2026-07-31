import sqlite3

from llm_studio.novels.migrations import initialize_novel_database
from llm_studio.writing.migrations import initialize_writing_database


def test_generation_records_table_is_idempotent(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_novel_database(db_path)
    initialize_writing_database(db_path)
    initialize_writing_database(db_path)

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

    assert "generation_records" in tables
    assert "novel_projects" in tables
    assert "idx_generation_records_project" in indexes
    assert "idx_generation_records_chapter" in indexes
