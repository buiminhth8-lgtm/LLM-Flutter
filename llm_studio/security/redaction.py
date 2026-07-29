"""Redaction helpers for logs, API errors, and public job payloads."""

from __future__ import annotations

import os
import re

_REDACTED = "<redacted>"

_SECRET_ASSIGNMENT_PATTERNS = (
    re.compile(r"(?i)\b(token|access_token|api_key)\s*=\s*([^\s&;,]+)"),
    re.compile(r"(?i)\b(token|access_token|api_key)\s*:\s*([^\s&;,]+)"),
)
_AUTHORIZATION_PATTERN = re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s,;]+)")


def redact_sensitive_text(text: str | None) -> str | None:
    """Redact common token forms while preserving useful error context."""

    if text is None:
        return None
    redacted = str(text)
    for env_name in ("HF_TOKEN", "HUGGINGFACE_HUB_TOKEN", "MODELSCOPE_API_TOKEN"):
        value = os.environ.get(env_name)
        if value:
            redacted = redacted.replace(value, _REDACTED)
    redacted = _AUTHORIZATION_PATTERN.sub(r"\1" + _REDACTED, redacted)
    for pattern in _SECRET_ASSIGNMENT_PATTERNS:
        redacted = pattern.sub(lambda match: f"{match.group(1)}={_REDACTED}", redacted)
    return redacted
