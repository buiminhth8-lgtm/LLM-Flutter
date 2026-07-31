"""Feature flag helpers."""

from __future__ import annotations

from typing import Any


def is_novel_studio_enabled(config: Any) -> bool:
    """Return whether Novel Studio is enabled.

    The flag is intentionally false by default. Stage 0 only prepares the
    engineering entry point; it must not expose Novel Studio business surfaces.
    """

    try:
        features = config.get("features", {}) if config is not None else {}
        if not isinstance(features, dict):
            return False
        novel = features.get("novel_studio", {})
        if not isinstance(novel, dict):
            return False
        return bool(novel.get("enabled", False))
    except Exception:
        return False


def is_revision_system_enabled(config: Any) -> bool:
    """Return whether the Stage 5 revision API should be exposed."""

    if not is_novel_studio_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        revision = features.get("revision_system", {})
        if not isinstance(revision, dict):
            return True
        return bool(revision.get("enabled", True))
    except Exception:
        return False
