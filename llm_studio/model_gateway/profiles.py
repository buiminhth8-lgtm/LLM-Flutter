"""Model profile DTOs, validation, and connection scrubbing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .errors import (
    MODEL_PROFILE_INVALID_PROVIDER,
    MODEL_PROFILE_SECRET_NOT_ALLOWED,
    MODEL_PROFILE_VALIDATION_FAILED,
    ModelGatewayError,
)

ALLOWED_PROVIDERS = frozenset({"local_runtime", "fake"})
RESERVED_PROVIDERS = frozenset({"openai_compatible", "deepseek"})
ALLOWED_STATUSES = frozenset({"enabled", "disabled", "archived"})

_SENSITIVE_KEY_MARKERS = (
    "api_key",
    "token",
    "authorization",
    "password",
    "secret",
    "cookie",
    "bearer",
)


def validate_provider(provider: str) -> str:
    value = str(provider or "").strip()
    if not value:
        raise ModelGatewayError(
            MODEL_PROFILE_VALIDATION_FAILED,
            "provider is required.",
            {"field": "provider"},
        )
    if value in RESERVED_PROVIDERS:
        raise ModelGatewayError(
            MODEL_PROFILE_INVALID_PROVIDER,
            f"Provider '{value}' is reserved for a future phase and cannot be enabled yet.",
            {"provider": value},
        )
    if value not in ALLOWED_PROVIDERS:
        raise ModelGatewayError(
            MODEL_PROFILE_INVALID_PROVIDER,
            f"Unsupported provider: {value}",
            {"provider": value},
        )
    return value


def validate_status(status: str) -> str:
    value = str(status or "enabled").strip() or "enabled"
    if value not in ALLOWED_STATUSES:
        raise ModelGatewayError(
            MODEL_PROFILE_VALIDATION_FAILED,
            f"Invalid profile status: {value}",
            {"field": "status", "status": value},
        )
    return value


def scrub_connection(connection: dict[str, Any]) -> dict[str, Any]:
    """Reject sensitive keys in connection data.

    API keys / tokens / Authorization / secrets must never be persisted for an
    online provider in this phase (and never in plain text).
    """
    if not isinstance(connection, dict):
        raise ModelGatewayError(
            MODEL_PROFILE_VALIDATION_FAILED,
            "connection must be an object.",
            {"field": "connection"},
        )
    sensitive = [
        key
        for key in connection
        if any(marker in str(key).lower() for marker in _SENSITIVE_KEY_MARKERS)
    ]
    if sensitive:
        raise ModelGatewayError(
            MODEL_PROFILE_SECRET_NOT_ALLOWED,
            "connection must not contain API keys, tokens, Authorization, or secrets.",
            {"fields": sorted(sensitive)},
        )
    return dict(connection)


@dataclass(frozen=True)
class ModelProfileCreate:
    name: str
    provider: str
    model: str | None = None
    description: str | None = None
    default_params: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)
    privacy_policy: dict[str, Any] = field(default_factory=dict)
    connection: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_default: bool = False
    status: str = "enabled"


@dataclass(frozen=True)
class ModelProfileUpdate:
    name: str | None = None
    description: str | None = None
    model: str | None = None
    status: str | None = None
    default_params: dict[str, Any] | None = None
    capabilities: dict[str, Any] | None = None
    privacy_policy: dict[str, Any] | None = None
    connection: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    is_default: bool | None = None
