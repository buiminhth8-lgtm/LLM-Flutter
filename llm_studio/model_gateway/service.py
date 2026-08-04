"""ModelGatewayService: provider registry and dispatch."""

from __future__ import annotations

import inspect
import time
from collections.abc import AsyncIterator
from dataclasses import replace
from typing import Any

from .errors import (
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_INVALID_REQUEST,
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    MODEL_GATEWAY_STREAM_FAILED,
    MODEL_PROFILE_DISABLED,
    MODEL_PROFILE_NOT_FOUND,
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
        profile_service: Any | None = None,
    ) -> None:
        self._providers: dict[str, ModelProvider] = dict(providers or {})
        self.profile_service = profile_service
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

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        self._validate_request(request)
        provider_name, resolved_request = self._resolve_request(request)
        provider = self.get_provider(provider_name)
        started = time.monotonic()
        try:
            result = await provider.generate(resolved_request)
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

    async def stream_generate(
        self,
        request: GenerateRequest,
    ) -> AsyncIterator[StreamChunk]:
        self._validate_request(request)
        provider_name, resolved_request = self._resolve_request(request)
        provider = self.get_provider(provider_name)
        streamer = provider.stream_generate(resolved_request)
        try:
            if inspect.isasyncgen(streamer):
                async for chunk in streamer:
                    yield chunk
            else:
                # Coroutine-style base implementation that raises immediately.
                await streamer
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

    def _resolve_request(
        self,
        request: GenerateRequest,
    ) -> tuple[str, GenerateRequest]:
        """Resolve provider / model / default params from profile_id when set."""
        if not request.profile_id:
            return resolve_provider_name(request.provider), request
        if self.profile_service is None:
            raise ModelGatewayError(
                MODEL_PROFILE_NOT_FOUND,
                "Profile resolution is not configured.",
                {"profile_id": request.profile_id},
            )
        profile = self.profile_service.get_profile(request.profile_id)
        if profile.status != "enabled":
            raise ModelGatewayError(
                MODEL_PROFILE_DISABLED,
                f"Model profile is not enabled: {request.profile_id}",
                {"profile_id": request.profile_id, "status": profile.status},
            )
        merged_params = {
            **profile.default_params,
            **request.generation_params,
        }
        resolved = replace(
            request,
            provider=profile.provider,
            model=request.model or profile.model,
            generation_params=merged_params,
        )
        return resolve_provider_name(profile.provider, profile), resolved
