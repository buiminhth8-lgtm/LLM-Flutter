"""Lightweight configuration migration helpers for Stage 12.

The project currently exposes configuration through `llm_studio.config` as a
module, so this helper intentionally lives beside it rather than under a
`llm_studio/config/` package. It is read-only unless callers explicitly write
the returned migrated payload.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

CURRENT_CONFIG_SCHEMA_VERSION = 1


def migrate_config_payload(data: dict[str, Any]) -> dict[str, Any]:
    """Return a migrated config payload without mutating the input."""

    migrated = deepcopy(data)
    migrated.setdefault("schema_version", CURRENT_CONFIG_SCHEMA_VERSION)
    features = migrated.setdefault("features", {})
    if isinstance(features, dict):
        features.setdefault("ui_productization", {"enabled": True})
        features.setdefault("windows_release", {"enabled": True})
        features.setdefault("backup_restore", {"enabled": True})
    storage = migrated.setdefault("storage", {})
    if isinstance(storage, dict):
        storage.setdefault("diagnostics_dir", "./data/diagnostics")
        storage.setdefault("backups_dir", "./data/backups")
    return migrated
