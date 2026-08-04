"""Business service for model profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import MODEL_PROFILE_NOT_FOUND, ModelGatewayError
from .profiles import ModelProfileCreate
from .repository import ModelProfileRepository
from .schemas import ModelProfile

BUILTIN_FAKE_PROFILE = ModelProfileCreate(
    name="Fake Test Model",
    provider="fake",
    model="fake",
    description="Test-only fake provider profile.",
    metadata={"builtin": True, "builtin_key": "builtin.fake.test.v1"},
    status="enabled",
)
BUILTIN_LOCAL_PROFILE = ModelProfileCreate(
    name="Local Runtime Default",
    provider="local_runtime",
    model=None,
    description="Default local runtime profile using the currently loaded local model.",
    metadata={"builtin": True, "builtin_key": "builtin.local_runtime.default.v1"},
    status="enabled",
)
BUILTIN_PROFILES = (BUILTIN_FAKE_PROFILE, BUILTIN_LOCAL_PROFILE)


class ModelProfileService:
    def __init__(
        self,
        db_path: str | Path,
        *,
        repository: ModelProfileRepository | None = None,
    ):
        self.db_path = Path(db_path)
        self.repository = repository or ModelProfileRepository(self.db_path)

    @classmethod
    def from_config(cls, config: Any) -> ModelProfileService:
        cfg = config.get("model_gateway", {}) if config is not None else {}
        fallback = (
            config.get("prompts", {}).get("db_path")
            or config.get("novels", {}).get("db_path", "./data/novels/novels.sqlite")
            if config is not None
            else "./data/novels/novels.sqlite"
        )
        return cls(cfg.get("db_path") or fallback)

    def ensure_builtin_profiles(self) -> dict[str, int]:
        summary = {"created": 0, "skipped": 0, "user_modified": 0}
        existing_by_key: dict[str, ModelProfile] = {}
        for profile in self.repository.list():
            key = profile.metadata.get("builtin_key")
            if isinstance(key, str) and key:
                existing_by_key[key] = profile
        for builtin in BUILTIN_PROFILES:
            key = builtin.metadata["builtin_key"]
            current = existing_by_key.get(key)
            if current is None:
                self.repository.create(builtin)
                summary["created"] += 1
                continue
            if current.metadata.get("builtin") is True and current.name == builtin.name:
                summary["skipped"] += 1
            else:
                summary["user_modified"] += 1
        if self.get_default_profile() is None:
            local = next(
                (
                    profile
                    for profile in self.repository.list()
                    if profile.metadata.get("builtin_key")
                    == "builtin.local_runtime.default.v1"
                ),
                None,
            )
            if local is not None:
                self.repository.set_default(local.id)
        return summary

    def create_profile(self, request: ModelProfileCreate) -> ModelProfile:
        return self.repository.create(request)

    def get_profile(self, profile_id: str) -> ModelProfile:
        profile = self.repository.get(profile_id)
        if profile is None:
            raise ModelGatewayError(
                MODEL_PROFILE_NOT_FOUND,
                f"Model profile not found: {profile_id}",
                {"profile_id": profile_id},
            )
        return profile

    def list_profiles(
        self,
        *,
        provider: str | None = None,
        status: str | None = None,
    ) -> list[ModelProfile]:
        return self.repository.list(provider=provider, status=status)

    def update_profile(
        self,
        profile_id: str,
        changes: dict[str, Any],
    ) -> ModelProfile:
        return self.repository.update(profile_id, changes)

    def archive_profile(self, profile_id: str) -> ModelProfile:
        return self.repository.archive(profile_id)

    def set_default_profile(self, profile_id: str) -> ModelProfile:
        return self.repository.set_default(profile_id)

    def get_default_profile(self) -> ModelProfile | None:
        return self.repository.get_default()
