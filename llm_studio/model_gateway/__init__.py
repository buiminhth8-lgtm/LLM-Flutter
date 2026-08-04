"""Model Gateway: provider-neutral model invocation layer."""

from __future__ import annotations

from .errors import (
    FAKE_PROVIDER_ERROR,
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_ERROR,
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_INVALID_REQUEST,
    MODEL_GATEWAY_PROFILE_NOT_FOUND,
    MODEL_GATEWAY_PROVIDER_DISABLED,
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    MODEL_GATEWAY_STREAM_FAILED,
    MODEL_GATEWAY_UNSUPPORTED_STREAMING,
    MODEL_PROFILE_DISABLED,
    MODEL_PROFILE_INVALID_PROVIDER,
    MODEL_PROFILE_NOT_FOUND,
    MODEL_PROFILE_SECRET_NOT_ALLOWED,
    MODEL_PROFILE_VALIDATION_FAILED,
    ModelGatewayError,
)
from .fake_provider import FakeProvider
from .local_provider import LocalRuntimeProvider
from .profile_service import ModelProfileService
from .profiles import ModelProfileCreate, ModelProfileUpdate
from .repository import ModelProfileRepository
from .schemas import GenerateRequest, GenerateResult, ModelProfile, StreamChunk
from .service import ModelGatewayService

__all__ = [
    "FAKE_PROVIDER_ERROR",
    "LOCAL_RUNTIME_UNAVAILABLE",
    "MODEL_GATEWAY_ERROR",
    "MODEL_GATEWAY_GENERATION_FAILED",
    "MODEL_GATEWAY_INVALID_REQUEST",
    "MODEL_GATEWAY_PROFILE_NOT_FOUND",
    "MODEL_GATEWAY_PROVIDER_DISABLED",
    "MODEL_GATEWAY_PROVIDER_NOT_FOUND",
    "MODEL_GATEWAY_STREAM_FAILED",
    "MODEL_GATEWAY_UNSUPPORTED_STREAMING",
    "MODEL_PROFILE_DISABLED",
    "MODEL_PROFILE_INVALID_PROVIDER",
    "MODEL_PROFILE_NOT_FOUND",
    "MODEL_PROFILE_SECRET_NOT_ALLOWED",
    "MODEL_PROFILE_VALIDATION_FAILED",
    "FakeProvider",
    "GenerateRequest",
    "GenerateResult",
    "LocalRuntimeProvider",
    "ModelGatewayError",
    "ModelGatewayService",
    "ModelProfile",
    "ModelProfileCreate",
    "ModelProfileRepository",
    "ModelProfileService",
    "ModelProfileUpdate",
    "StreamChunk",
]
