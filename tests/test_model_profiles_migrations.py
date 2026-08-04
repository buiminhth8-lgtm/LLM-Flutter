import sqlite3

from llm_studio.model_gateway.migrations import initialize_model_gateway_database


def _tables(db_path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    return {row[0] for row in rows}


def _indexes(db_path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'index'"
        ).fetchall()
    return {row[0] for row in rows}


def test_model_profiles_table_is_created(tmp_path):
    db_path = tmp_path / "gateway.sqlite"

    initialize_model_gateway_database(db_path)

    assert "model_profiles" in _tables(db_path)


def test_model_profiles_indexes_are_created(tmp_path):
    db_path = tmp_path / "gateway.sqlite"

    initialize_model_gateway_database(db_path)

    indexes = _indexes(db_path)
    assert "idx_model_profiles_provider" in indexes
    assert "idx_model_profiles_status" in indexes
    assert "idx_model_profiles_is_default" in indexes


def test_model_profiles_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "gateway.sqlite"

    initialize_model_gateway_database(db_path)
    initialize_model_gateway_database(db_path)

    assert "model_profiles" in _tables(db_path)
