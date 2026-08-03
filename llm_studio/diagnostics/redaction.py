"""Redaction helpers for Stage 12 diagnostics."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SECRET_KEY_PATTERNS = (
    "api_key",
    "apikey",
    "authorization",
    "cookie",
    "password",
    "secret",
)

SECRET_VALUE_RE = re.compile(
    r"(?i)(sk-[a-z0-9_-]{8,}|bearer\s+[a-z0-9._-]{8,}|x-api-key\s*[:=]\s*\S+|authorization\s*[:=]\s*\S+)"
)


def redact_text(value: str) -> str:
    return SECRET_VALUE_RE.sub("<redacted>", value)


def redact_path(path: str | Path, *, label: str = "path") -> str:
    """Return a non-sensitive path summary without local absolute roots."""

    candidate = Path(path)
    try:
        relative_home = candidate.resolve().relative_to(Path.home().resolve())
        return str(Path("%USERPROFILE%") / relative_home)
    except Exception:
        pass
    name = candidate.name or "<root>"
    return f"<redacted-{label}>/{name}"


def _is_secret_key(key: str) -> bool:
    lowered = key.lower()
    if any(pattern in lowered for pattern in SECRET_KEY_PATTERNS):
        return True
    return lowered in {"token", "bearer_token", "access_token", "refresh_token"} or lowered.endswith("_token")


def _is_path_key(key: str) -> bool:
    lowered = key.lower()
    return (
        "path" in lowered
        or lowered.endswith("_dir")
        or lowered.endswith("_file")
        or lowered.endswith("_cache")
        or lowered in {"metadata_cache", "cache_dir"}
    )


def redact_mapping(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if _is_secret_key(key_text):
                redacted[key] = "<redacted>"
            elif _is_path_key(key_text) and isinstance(item, str | Path):
                redacted[key] = redact_path(str(item))
            else:
                redacted[key] = redact_mapping(item)
        return redacted
    if isinstance(value, list):
        return [redact_mapping(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value
