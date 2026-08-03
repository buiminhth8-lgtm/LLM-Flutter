import sqlite3

from llm_studio.context.migrations import initialize_context_database
from llm_studio.memory.migrations import MEMORY_TABLES, initialize_memory_database


def test_memory_stage10_tables_initialize(tmp_path):
    db_path = tmp_path / "memory.sqlite"
    initialize_memory_database(db_path)

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'virtual table')"
            )
        }

    for table in MEMORY_TABLES:
        assert table in tables


def test_context_records_have_optional_retrieval_id(tmp_path):
    db_path = tmp_path / "context.sqlite"
    initialize_context_database(db_path)

    with sqlite3.connect(db_path) as conn:
        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(context_assembly_records)").fetchall()
        }

    assert "retrieval_id" in columns

