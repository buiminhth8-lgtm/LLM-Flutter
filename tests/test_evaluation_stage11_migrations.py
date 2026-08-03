import sqlite3

from llm_studio.evaluation.migrations import EVALUATION_TABLES, initialize_evaluation_database


def test_evaluation_stage11_tables_initialize(tmp_path):
    db = tmp_path / "evaluation.sqlite"
    initialize_evaluation_database(db)
    with sqlite3.connect(db) as conn:
        names = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
    for table in EVALUATION_TABLES:
        assert table in names

