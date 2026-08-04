"""LocalRuntimeProvider wrapping the existing local runtime / bridge."""

from __future__ import annotations

import inspect
import time
import uuid
from collections.abc import AsyncIterator
from typing import Any

from .errors import (
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_STREAM_FAILED,
    MODEL_GATEWAY_UNSUPPORTED_STREAMING,
    ModelGatewayError,
)
from .provider_base import BaseModelProvider
from .schemas import GenerateRequest, GenerateResult, StreamChunk

_TEXT_KEYS = ("text", "output", "content", "generated_text")
_USAGE_INPUT_KEYS = ("prompt_tokens", "input_tokens")
_USAGE_OUTPUT_KEYS = ("completion_tokens", "output_tokens")


async def _maybe_await(value: Any) -> Any:
    """Await ``value`` when it is awaitable, otherwise return it unchanged."""
    if inspect.isawaitable(value):
        return await value
    return value


async def _async_iter(value: Any) -> AsyncIterator[Any]:
    """Iterate over both async generators and sync iterables."""
    if inspect.isasyncgen(value):
        async for item in value:
            yield item
    else:
        for item in value:
            yield item


class LocalRuntimeProvider(BaseModelProvider):
    """Thin wrapper around an existing runtime or runtime bridge.

    The wrapper does not change runtime behavior and does not force model
    loading. Supported injected shapes, in priority order:

    1. ``runtime_bridge.generate_text(model_id, prompt, generation_params, adapter_id)``
    2. ``runtime_bridge.generate(model_id=..., prompt=..., generation_params=..., adapter_id=...)``
    3. ``runtime.generate_text(prompt, **params)``
    4. ``runtime.generate(prompt, **params)``
    """

    provider_name = "local_runtime"

    def __init__(self, runtime_bridge: Any = None, runtime: Any = None):
        self.runtime_bridge = runtime_bridge
        self.runtime = runtime

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        self._require_runtime()
        started = time.monotonic()
        try:
            output = await self._invoke_generate(request)
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise self._wrap_error(exc, stream=False) from exc
        return self._normalize_result(request, output, started)

    async def stream_generate(
        self,
        request: GenerateRequest,
    ) -> AsyncIterator[StreamChunk]:
        self._require_runtime()
        try:
            bridge = self.runtime_bridge
            if bridge is not None and (
                hasattr(bridge, "_stream_text_impl") or hasattr(bridge, "stream_text")
            ):
                stream_fn = (
                    bridge._stream_text_impl
                    if hasattr(bridge, "_stream_text_impl")
                    else bridge.stream_text
                )
                streamer = stream_fn(
                    generation_id=f"gateway-{uuid.uuid4().hex[:12]}",
                    model_id=request.model,
                    prompt=request.prompt,
                    generation_params=request.generation_params,
                    adapter_id=request.adapter_id,
                )
                async for chunk in _async_iter(streamer):
                    yield StreamChunk(
                        delta=str(chunk),
                        event="delta",
                        provider=self.provider_name,
                        model=request.model,
                    )
                yield self._done_chunk(request)
                return
            if self.runtime is not None and hasattr(self.runtime, "generate_stream"):
                streamer = self.runtime.generate_stream(
                    request.prompt,
                    **self._runtime_kwargs(request.generation_params),
                )
                async for chunk in _async_iter(streamer):
                    yield StreamChunk(
                        delta=str(chunk),
                        event="delta",
                        provider=self.provider_name,
                        model=request.model,
                    )
                yield self._done_chunk(request)
                return
        except ModelGatewayError:
            raise
        except Exception as exc:
            raise self._wrap_error(exc, stream=True) from exc
        raise ModelGatewayError(
            MODEL_GATEWAY_UNSUPPORTED_STREAMING,
            "LocalRuntimeProvider has no streamable runtime or bridge.",
            {"provider": self.provider_name},
        )

    def get_capabilities(self) -> dict[str, Any]:
        streaming = False
        if self.runtime_bridge is not None and (
            hasattr(self.runtime_bridge, "_stream_text_impl")
            or hasattr(self.runtime_bridge, "stream_text")
        ):
            streaming = True
        if self.runtime is not None and hasattr(self.runtime, "generate_stream"):
            streaming = True
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

    async def _invoke_generate(self, request: GenerateRequest) -> Any:
        bridge = self.runtime_bridge
        if bridge is not None:
            if hasattr(bridge, "_generate_text_impl"):
                return await _maybe_await(
                    bridge._generate_text_impl(
                        generation_id=f"gateway-{uuid.uuid4().hex[:12]}",
                        model_id=request.model,
                        prompt=request.prompt,
                        generation_params=request.generation_params,
                        adapter_id=request.adapter_id,
                    )
                )
            if hasattr(bridge, "generate_text"):
                return await _maybe_await(
                    bridge.generate_text(
                        generation_id=f"gateway-{uuid.uuid4().hex[:12]}",
                        model_id=request.model,
                        prompt=request.prompt,
                        generation_params=request.generation_params,
                        adapter_id=request.adapter_id,
                    )
                )
            if hasattr(bridge, "generate"):
                return await _maybe_await(
                    bridge.generate(
                        model_id=request.model,
                        prompt=request.prompt,
                        generation_params=request.generation_params,
                        adapter_id=request.adapter_id,
                    )
                )
        if self.runtime is not None:
            kwargs = self._runtime_kwargs(request.generation_params)
            if hasattr(self.runtime, "generate_text"):
                return await _maybe_await(self.runtime.generate_text(request.prompt, **kwargs))
            if hasattr(self.runtime, "generate"):
                return await _maybe_await(self.runtime.generate(request.prompt, **kwargs))
        raise ModelGatewayError(
            LOCAL_RUNTIME_UNAVAILABLE,
            "Local runtime is not configured.",
            {"provider": self.provider_name},
        )

    def _normalize_result(
        self,
        request: GenerateRequest,
        output: Any,
        started: float,
    ) -> GenerateResult:
        if isinstance(output, dict):
            text = ""
            for key in _TEXT_KEYS:
                if output.get(key) is not None:
                    text = str(output[key])
                    break
            finish_reason = output.get("finish_reason")
            usage = output.get("usage") if isinstance(output.get("usage"), dict) else {}
            latency_ms = output.get("latency_ms")
            extra_keys = sorted(
                set(output)
                - set(_TEXT_KEYS)
                - {"finish_reason", "usage", "latency_ms"}
            )
            return self._result(
                request,
                text,
                finish_reason,
                latency_ms,
                usage,
                started,
                {"runtime_result_keys": extra_keys},
            )
        text = getattr(output, "text", None)
        if text is None:
            text = str(output)
        finish_reason = getattr(output, "finish_reason", None) or "stop"
        latency_ms = getattr(output, "latency_ms", None)
        usage = getattr(output, "usage", None) or getattr(output, "raw_usage", None)
        if not isinstance(usage, dict):
            usage = {}
        return self._result(
            request,
            str(text),
            finish_reason,
            latency_ms,
            usage,
            started,
            {"runtime_type": type(output).__name__},
        )

    def _result(
        self,
        request: GenerateRequest,
        text: str,
        finish_reason: Any,
        latency_ms: Any,
        usage: dict[str, Any],
        started: float,
        metadata: dict[str, Any],
    ) -> GenerateResult:
        if latency_ms is None:
            latency_ms = int((time.monotonic() - started) * 1000)
        return GenerateResult(
            text=text,
            finish_reason=str(finish_reason) if finish_reason is not None else None,
            provider=self.provider_name,
            model=request.model,
            profile_id=request.profile_id,
            input_tokens=self._usage_value(usage, _USAGE_INPUT_KEYS),
            output_tokens=self._usage_value(usage, _USAGE_OUTPUT_KEYS),
            latency_ms=int(latency_ms),
            warnings=[],
            raw_usage=usage,
            metadata={**metadata, "provider": self.provider_name},
        )

    def _done_chunk(self, request: GenerateRequest) -> StreamChunk:
        return StreamChunk(
            delta="",
            event="done",
            provider=self.provider_name,
            model=request.model,
            finish_reason="stop",
        )

    def _wrap_error(self, exc: Exception, *, stream: bool) -> ModelGatewayError:
        details: dict[str, Any] = {
            "provider": self.provider_name,
            "original_type": type(exc).__name__,
        }
        code = getattr(exc, "code", None)
        if code:
            details["original_code"] = str(code)
        gateway_code = MODEL_GATEWAY_STREAM_FAILED if stream else MODEL_GATEWAY_GENERATION_FAILED
        kind = "streaming" if stream else "generation"
        return ModelGatewayError(
            gateway_code,
            f"Local runtime {kind} failed: {exc}",
            details,
        )

    def _require_runtime(self) -> None:
        if self.runtime_bridge is None and self.runtime is None:
            raise ModelGatewayError(
                LOCAL_RUNTIME_UNAVAILABLE,
                "Local runtime is not configured.",
                {"provider": self.provider_name},
            )

    @staticmethod
    def _usage_value(usage: dict[str, Any], keys: tuple[str, ...]) -> int | None:
        for key in keys:
            value = usage.get(key)
            if value is not None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None
        return None

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
