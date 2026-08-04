"""SQLite repository for model profiles."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from typing import Any

from .errors import (
    MODEL_PROFILE_NOT_FOUND,
    MODEL_PROFILE_VALIDATION_FAILED,
    ModelGatewayError,
)
from .migrations import initialize_model_gateway_database
from .profiles import ModelProfileCreate, scrub_connection, validate_provider, validate_status
from .schemas import ModelProfile


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _loads(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


class ModelProfileRepository:
    """Persist and query model profiles (no credentials are ever stored)."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._lock = RLock()
        initialize_model_gateway_database(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def create(self, profile_create: ModelProfileCreate) -> ModelProfile:
        name = str(profile_create.name or "").strip()
        if not name:
            raise ModelGatewayError(
                MODEL_PROFILE_VALIDATION_FAILED,
                "name is required.",
                {"field": "name"},
            )
        provider = validate_provider(profile_create.provider)
        status = validate_status(profile_create.status)
        connection = scrub_connection(profile_create.connection)
        now = utc_now()
        profile_id = str(uuid.uuid4())
        is_default = 1 if profile_create.is_default else 0
        with self._lock, self._connect() as conn:
            if is_default:
                conn.execute("UPDATE model_profiles SET is_default = 0")
            conn.execute(
                """
                INSERT INTO model_profiles (
                    id, name, provider, model, status, description,
                    default_params_json, capabilities_json, privacy_policy_json,
                    connection_json, metadata_json, is_default, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id,
                    name,
                    provider,
                    profile_create.model,
                    status,
                    profile_create.description,
                    json.dumps(profile_create.default_params or {}, ensure_ascii=False),
                    json.dumps(profile_create.capabilities or {}, ensure_ascii=False),
                    json.dumps(profile_create.privacy_policy or {}, ensure_ascii=False),
                    json.dumps(connection, ensure_ascii=False),
                    json.dumps(profile_create.metadata or {}, ensure_ascii=False),
                    is_default,
                    now,
                    now,
                ),
            )
        return self.get(profile_id)

    def get(self, profile_id: str) -> ModelProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM model_profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
        return self._row_to_profile(row) if row is not None else None

    def list(
        self,
        *,
        provider: str | None = None,
        status: str | None = None,
    ) -> list[ModelProfile]:
        clauses: list[str] = []
        params: list[Any] = []
        if provider:
            clauses.append("provider = ?")
            params.append(provider)
        if status:
            clauses.append("status = ?")
            params.append(status)
        else:
            clauses.append("status != 'archived'")
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM model_profiles{where} ORDER BY updated_at DESC",
                params,
            ).fetchall()
        return [self._row_to_profile(row) for row in rows]

    def update(self, profile_id: str, changes: dict[str, Any]) -> ModelProfile:
        self._require_profile(profile_id)
        if "provider" in changes:
            raise ModelGatewayError(
                MODEL_PROFILE_VALIDATION_FAILED,
                "provider cannot be changed after creation.",
                {"field": "provider"},
            )
        if "status" in changes and changes["status"] is not None:
            changes["status"] = validate_status(changes["status"])
        if "connection" in changes and changes["connection"] is not None:
            changes["connection"] = scrub_connection(changes["connection"])
        mapping = {
            "name": "name",
            "description": "description",
            "model": "model",
            "status": "status",
            "default_params": "default_params_json",
            "capabilities": "capabilities_json",
            "privacy_policy": "privacy_policy_json",
            "connection": "connection_json",
            "metadata": "metadata_json",
            "is_default": "is_default",
        }
        assignments: dict[str, Any] = {}
        for key, column in mapping.items():
            if key not in changes or changes[key] is None:
                continue
            value = changes[key]
            if key in {
                "default_params",
                "capabilities",
                "privacy_policy",
                "connection",
                "metadata",
            }:
                if not isinstance(value, dict):
                    raise ModelGatewayError(
                        MODEL_PROFILE_VALIDATION_FAILED,
                        f"{key} must be an object.",
                        {"field": key},
                    )
                assignments[column] = json.dumps(value, ensure_ascii=False)
            elif key == "is_default":
                assignments[column] = 1 if value else 0
            else:
                assignments[column] = value
        if not assignments:
            return self.get(profile_id)
        assignments["updated_at"] = utc_now()
        set_default = changes.get("is_default") is True
        with self._lock, self._connect() as conn:
            if set_default:
                conn.execute("UPDATE model_profiles SET is_default = 0")
            assignments_sql = ", ".join(f"{key} = ?" for key in assignments)
            conn.execute(
                f"UPDATE model_profiles SET {assignments_sql} WHERE id = ?",
                [*assignments.values(), profile_id],
            )
        return self.get(profile_id)

    def archive(self, profile_id: str) -> ModelProfile:
        self._require_profile(profile_id)
        return self.update(
            profile_id,
            {"status": "archived", "is_default": False},
        )

    def delete(self, profile_id: str) -> None:
        """Soft delete: archive the profile to preserve history."""
        self.archive(profile_id)

    def get_default(self) -> ModelProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM model_profiles WHERE is_default = 1 AND status = 'enabled' "
                "ORDER BY updated_at DESC LIMIT 1",
            ).fetchone()
        return self._row_to_profile(row) if row is not None else None

    def set_default(self, profile_id: str) -> ModelProfile:
        profile = self._require_profile(profile_id)
        if profile.status != "enabled":
            raise ModelGatewayError(
                MODEL_PROFILE_VALIDATION_FAILED,
                "Only an enabled profile can be the default.",
                {"profile_id": profile_id, "status": profile.status},
            )
        with self._lock, self._connect() as conn:
            conn.execute("UPDATE model_profiles SET is_default = 0")
            conn.execute(
                "UPDATE model_profiles SET is_default = 1, updated_at = ? WHERE id = ?",
                (utc_now(), profile_id),
            )
        return self.get(profile_id)

    def _require_profile(self, profile_id: str) -> ModelProfile:
        profile = self.get(profile_id)
        if profile is None:
            raise ModelGatewayError(
                MODEL_PROFILE_NOT_FOUND,
                f"Model profile not found: {profile_id}",
                {"profile_id": profile_id},
            )
        return profile

    @staticmethod
    def _row_to_profile(row: sqlite3.Row) -> ModelProfile:
        data = dict(row)
        return ModelProfile(
            id=data["id"],
            name=data["name"],
            provider=data["provider"],
            model=data["model"],
            status=data["status"],
            description=data["description"],
            default_params=_loads(data["default_params_json"], {}),
            capabilities=_loads(data["capabilities_json"], {}),
            privacy_policy=_loads(data["privacy_policy_json"], {}),
            connection=_loads(data["connection_json"], {}),
            metadata=_loads(data["metadata_json"], {}),
            is_default=bool(data["is_default"]),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )
