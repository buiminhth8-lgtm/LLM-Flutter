"""ModelGatewayService: provider registry and dispatch."""

from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from .errors import (
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_INVALID_REQUEST,
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    MODEL_GATEWAY_STREAM_FAILED,
    ModelGatewayError,
)
from .fake_provider import FakeProvider
from .provider_base import ModelProvider
from .routing import resolve_provider_name
from .schemas import GenerateRequest, GenerateResult, StreamChunk


class ModelGatewayService:
    """Routes generation requests to registered providers."""

    def __init__(
        self,
        providers: dict[str, ModelProvider] | None = None,
    ) -> None:
        self._providers: dict[str, ModelProvider] = dict(providers or {})
        if "fake" not in self._providers:
            self.register_provider(FakeProvider())

    def register_provider(self, provider: ModelProvider) -> None:
        self._providers[provider.provider_name] = provider

    def get_provider(self, provider_name: str) -> ModelProvider:
        provider = self._providers.get(provider_name)
        if provider is None:
            raise ModelGatewayError(
                MODEL_GATEWAY_PROVIDER_NOT_FOUND,
                f"Model provider not found: {provider_name}",
                {"provider": provider_name},
            )
        return provider

    def list_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "capabilities": provider.get_capabilities(),
                "health": provider.health_check(),
            }
            for name, provider in sorted(self._providers.items())
        ]

    def generate(self, request: GenerateRequest) -> GenerateResult:
        self._validate_request(request)
        provider_name = resolve_provider_name(request.provider)
        provider = self.get_provider(provider_name)
        started = time.monotonic()
        try:
            result = provider.generate(request)
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError(
                MODEL_GATEWAY_GENERATION_FAILED,
                f"Generation failed via provider '{provider_name}': {exc}",
                {
                    "provider": provider_name,
                    "original_type": type(exc).__name__,
                },
            ) from exc
        if result.latency_ms is None:
            result = GenerateResult(
                text=result.text,
                finish_reason=result.finish_reason,
                provider=result.provider or provider_name,
                model=result.model,
                profile_id=result.profile_id,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                latency_ms=int((time.monotonic() - started) * 1000),
                warnings=result.warnings,
                raw_usage=result.raw_usage,
                metadata=result.metadata,
            )
        return result

    def stream_generate(
        self,
        request: GenerateRequest,
    ) -> Iterator[StreamChunk]:
        self._validate_request(request)
        provider_name = resolve_provider_name(request.provider)
        provider = self.get_provider(provider_name)
        try:
            yield from provider.stream_generate(request)
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError(
                MODEL_GATEWAY_STREAM_FAILED,
                f"Streaming failed via provider '{provider_name}': {exc}",
                {
                    "provider": provider_name,
                    "original_type": type(exc).__name__,
                },
            ) from exc

    @staticmethod
    def _validate_request(request: GenerateRequest) -> None:
        if not (request.prompt or "").strip():
            raise ModelGatewayError(
                MODEL_GATEWAY_INVALID_REQUEST,
                "GenerateRequest.prompt must not be empty.",
                {"field": "prompt"},
            )
