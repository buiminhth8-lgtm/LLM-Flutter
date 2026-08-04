"""LocalRuntimeProvider wrapping the existing local runtime / bridge."""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from collections.abc import Iterator
from typing import Any

from .errors import (
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_UNSUPPORTED_STREAMING,
    ModelGatewayError,
)
from .provider_base import BaseModelProvider
from .schemas import GenerateRequest, GenerateResult, StreamChunk


def _maybe_await(value: Any) -> Any:
    """Run an awaitable from a sync context (no running loop expected)."""
    if inspect.isawaitable(value):
        return asyncio.run(value)
    return value


class LocalRuntimeProvider(BaseModelProvider):
    """Thin wrapper around an existing runtime or runtime bridge.

    The wrapper does not change runtime behavior and does not force model
    loading. Prefer ``runtime_bridge.generate_text``; fall back to
    ``runtime.generate`` when only a raw runner is injected.
    """

    provider_name = "local_runtime"

    def __init__(self, runtime_bridge: Any = None, runtime: Any = None):
        self.runtime_bridge = runtime_bridge
        self.runtime = runtime

    def generate(self, request: GenerateRequest) -> GenerateResult:
        self._require_runtime()
        started = time.monotonic()
        try:
            if self.runtime_bridge is not None and hasattr(
                self.runtime_bridge,
                "generate_text",
            ):
                result = _maybe_await(
                    self.runtime_bridge.generate_text(
                        generation_id=f"gateway-{uuid.uuid4().hex[:12]}",
                        model_id=request.model,
                        prompt=request.prompt,
                        generation_params=request.generation_params,
                        adapter_id=request.adapter_id,
                    )
                )
                return self._to_result(request, result, started)
            if self.runtime is not None and hasattr(self.runtime, "generate"):
                text = _maybe_await(
                    self.runtime.generate(
                        request.prompt,
                        **self._runtime_kwargs(request.generation_params),
                    )
                )
                return GenerateResult(
                    text=str(text),
                    finish_reason="stop",
                    provider=self.provider_name,
                    model=request.model,
                    profile_id=request.profile_id,
                    latency_ms=int((time.monotonic() - started) * 1000),
                )
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError(
                MODEL_GATEWAY_GENERATION_FAILED,
                f"Local runtime generation failed: {exc}",
                {
                    "provider": self.provider_name,
                    "original_type": type(exc).__name__,
                },
            ) from exc
        raise ModelGatewayError(
            LOCAL_RUNTIME_UNAVAILABLE,
            "Local runtime is not configured.",
            {"provider": self.provider_name},
        )

    def stream_generate(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        self._require_runtime()
        bridge = self.runtime_bridge
        if bridge is None or not hasattr(bridge, "stream_text"):
            raise ModelGatewayError(
                MODEL_GATEWAY_UNSUPPORTED_STREAMING,
                "LocalRuntimeProvider has no streamable runtime bridge.",
                {"provider": self.provider_name},
            )
        stream_fn = bridge.stream_text
        if inspect.iscoroutinefunction(stream_fn) or inspect.isasyncgenfunction(stream_fn):
            # The real WritingRuntimeBridge exposes an async generator; wiring
            # async streaming through the sync provider API is deferred.
            raise ModelGatewayError(
                MODEL_GATEWAY_UNSUPPORTED_STREAMING,
                "Async runtime bridge streaming is not wired in this phase.",
                {"provider": self.provider_name},
            )
        try:
            generator = stream_fn(
                generation_id=f"gateway-{uuid.uuid4().hex[:12]}",
                model_id=request.model,
                prompt=request.prompt,
                generation_params=request.generation_params,
                adapter_id=request.adapter_id,
            )
            for chunk in generator:
                yield StreamChunk(
                    delta=str(chunk),
                    event="delta",
                    provider=self.provider_name,
                    model=request.model,
                )
            yield StreamChunk(
                delta="",
                event="done",
                provider=self.provider_name,
                model=request.model,
                finish_reason="stop",
            )
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise ModelGatewayError(
                MODEL_GATEWAY_GENERATION_FAILED,
                f"Local runtime streaming failed: {exc}",
                {
                    "provider": self.provider_name,
                    "original_type": type(exc).__name__,
                },
            ) from exc

    def get_capabilities(self) -> dict[str, Any]:
        streaming = False
        if self.runtime_bridge is not None and hasattr(
            self.runtime_bridge,
            "stream_text",
        ):
            stream_fn = self.runtime_bridge.stream_text
            streaming = not (
                inspect.iscoroutinefunction(stream_fn)
                or inspect.isasyncgenfunction(stream_fn)
            )
        return {
            "provider": self.provider_name,
            "streaming": streaming,
            "supports_adapter": True,
            "usage": False,
        }

    def health_check(self) -> dict[str, Any]:
        configured = self.runtime_bridge is not None or self.runtime is not None
        return {
            "provider": self.provider_name,
            "status": "ok" if configured else "unavailable",
            "runtime_bridge": self.runtime_bridge is not None,
            "runtime": self.runtime is not None,
        }

    def _require_runtime(self) -> None:
        if self.runtime_bridge is None and self.runtime is None:
            raise ModelGatewayError(
                LOCAL_RUNTIME_UNAVAILABLE,
                "Local runtime is not configured.",
                {"provider": self.provider_name},
            )

    def _to_result(
        self,
        request: GenerateRequest,
        result: Any,
        started: float,
    ) -> GenerateResult:
        text = result.text if hasattr(result, "text") else str(result)
        finish_reason = getattr(result, "finish_reason", None) or "stop"
        latency_ms = getattr(result, "latency_ms", None)
        if latency_ms is None:
            latency_ms = int((time.monotonic() - started) * 1000)
        return GenerateResult(
            text=str(text),
            finish_reason=str(finish_reason),
            provider=self.provider_name,
            model=request.model,
            profile_id=request.profile_id,
            input_tokens=None,
            output_tokens=None,
            latency_ms=latency_ms,
            raw_usage={},
        )

    @staticmethod
    def _runtime_kwargs(params: dict[str, Any]) -> dict[str, Any]:
        supported = {
            "temperature",
            "top_p",
            "max_tokens",
            "repetition_penalty",
            "stop",
        }
        return {key: value for key, value in (params or {}).items() if key in supported}
