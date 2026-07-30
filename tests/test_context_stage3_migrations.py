import sqlite3

from llm_studio.context.migrations import CONTEXT_TABLES, initialize_context_database
from llm_studio.novels.migrations import initialize_novel_database


def test_context_migration_is_idempotent_and_preserves_novel_tables(tmp_path):
    db_path = tmp_path / "novels.sqlite"
    initialize_novel_database(db_path)
    initialize_context_database(db_path)
    initialize_context_database(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert set(CONTEXT_TABLES).issubset(tables)
    assert "novel_projects" in tables
    assert "novel_chapters" in tables
