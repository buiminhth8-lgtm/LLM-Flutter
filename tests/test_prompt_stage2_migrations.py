import sqlite3

from llm_studio.prompts.migrations import PROMPT_TABLES, initialize_prompt_database


def test_prompt_tables_initialize_idempotently(tmp_path):
    db_path = tmp_path / "prompts.sqlite"

    initialize_prompt_database(db_path)
    initialize_prompt_database(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert set(PROMPT_TABLES).issubset(tables)
