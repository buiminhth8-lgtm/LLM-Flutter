"""SQLite migrations for Model Gateway model profiles."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def initialize_model_gateway_database(db_path: str | Path) -> None:
    """Create the model_profiles table and indexes (idempotent)."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS model_profiles (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              provider TEXT NOT NULL,
              model TEXT,
              status TEXT NOT NULL DEFAULT 'enabled',
              description TEXT,
              default_params_json TEXT NOT NULL DEFAULT '{}',
              capabilities_json TEXT NOT NULL DEFAULT '{}',
              privacy_policy_json TEXT NOT NULL DEFAULT '{}',
              connection_json TEXT NOT NULL DEFAULT '{}',
              metadata_json TEXT NOT NULL DEFAULT '{}',
              is_default INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_model_profiles_provider
            ON model_profiles(provider);
            CREATE INDEX IF NOT EXISTS idx_model_profiles_status
            ON model_profiles(status);
            CREATE INDEX IF NOT EXISTS idx_model_profiles_is_default
            ON model_profiles(is_default);
            """
        )
