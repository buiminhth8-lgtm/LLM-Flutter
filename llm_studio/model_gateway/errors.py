"""Model Gateway error codes and exceptions."""

from __future__ import annotations

import json
from typing import Any

MODEL_GATEWAY_ERROR = "MODEL_GATEWAY_ERROR"
MODEL_GATEWAY_PROVIDER_NOT_FOUND = "MODEL_GATEWAY_PROVIDER_NOT_FOUND"
MODEL_GATEWAY_PROFILE_NOT_FOUND = "MODEL_GATEWAY_PROFILE_NOT_FOUND"
MODEL_GATEWAY_INVALID_REQUEST = "MODEL_GATEWAY_INVALID_REQUEST"
MODEL_GATEWAY_GENERATION_FAILED = "MODEL_GATEWAY_GENERATION_FAILED"
MODEL_GATEWAY_STREAM_FAILED = "MODEL_GATEWAY_STREAM_FAILED"
MODEL_GATEWAY_PROVIDER_DISABLED = "MODEL_GATEWAY_PROVIDER_DISABLED"
MODEL_GATEWAY_UNSUPPORTED_STREAMING = "MODEL_GATEWAY_UNSUPPORTED_STREAMING"
LOCAL_RUNTIME_UNAVAILABLE = "LOCAL_RUNTIME_UNAVAILABLE"
FAKE_PROVIDER_ERROR = "FAKE_PROVIDER_ERROR"
MODEL_PROFILE_NOT_FOUND = "MODEL_PROFILE_NOT_FOUND"
MODEL_PROFILE_DISABLED = "MODEL_PROFILE_DISABLED"
MODEL_PROFILE_INVALID_PROVIDER = "MODEL_PROFILE_INVALID_PROVIDER"
MODEL_PROFILE_VALIDATION_FAILED = "MODEL_PROFILE_VALIDATION_FAILED"
MODEL_PROFILE_SECRET_NOT_ALLOWED = "MODEL_PROFILE_SECRET_NOT_ALLOWED"


def _json_safe(value: Any) -> Any:
    """Recursively convert values to JSON-serializable primitives."""
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


class ModelGatewayError(Exception):
    """Base error for Model Gateway.

    ``code`` is a stable machine-readable string, ``details`` is guaranteed
    JSON-serializable so it can be forwarded to an API error mapper later.
    """

    def __init__(
        self,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.code = code or MODEL_GATEWAY_ERROR
        self.message = message
        self.details = _json_safe(details or {})

    def __str__(self) -> str:
        return f"{self.code}: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
