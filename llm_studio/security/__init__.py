"""Security utilities."""

from __future__ import annotations

import hashlib

from .paths import PathSecurityError, resolve_allowed_path
from .redaction import redact_sensitive_text


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def redact_secret(value: str | None) -> str:
    if not value:
        return ""
    text = str(value)
    if len(text) <= 8:
        return "***"
    return f"{text[:4]}...{text[-4:]}"


__all__ = [
    "PathSecurityError",
    "hash_api_key",
    "redact_secret",
    "redact_sensitive_text",
    "resolve_allowed_path",
]
