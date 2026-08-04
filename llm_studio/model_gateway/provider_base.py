"""ModelProvider abstraction."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from .errors import MODEL_GATEWAY_UNSUPPORTED_STREAMING, ModelGatewayError
from .schemas import GenerateRequest, GenerateResult, StreamChunk


@runtime_checkable
class ModelProvider(Protocol):
    """Contract implemented by every model provider."""

    provider_name: str

    async def generate(self, request: GenerateRequest) -> GenerateResult: ...

    def stream_generate(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]: ...

    def get_capabilities(self) -> dict[str, Any]: ...

    def health_check(self) -> dict[str, Any]: ...


class BaseModelProvider:
    """Convenience base with safe defaults for streaming / health checks."""

    provider_name = "base"

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        raise NotImplementedError

    async def stream_generate(
        self,
        request: GenerateRequest,
    ) -> AsyncIterator[StreamChunk]:
        raise ModelGatewayError(
            MODEL_GATEWAY_UNSUPPORTED_STREAMING,
            f"Provider '{self.provider_name}' does not support streaming.",
            {"provider": self.provider_name},
        )

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "streaming": False,
            "supports_adapter": False,
            "usage": False,
        }

    def health_check(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "ok"}
