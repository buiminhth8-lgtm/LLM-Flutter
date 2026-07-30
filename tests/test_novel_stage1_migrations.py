import sqlite3

from llm_studio.novels.migrations import NOVEL_TABLES, initialize_novel_database


def test_novel_migrations_create_expected_tables(tmp_path):
    db_path = tmp_path / "novels.sqlite"

    initialize_novel_database(db_path)
    initialize_novel_database(db_path)

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    tables = {row[0] for row in rows}

    assert set(NOVEL_TABLES).issubset(tables)
    assert "jobs" not in tables
    assert "downloads" not in tables
