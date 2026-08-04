"""Adapter between WritingService and the Model Gateway.

The public ``generate_text`` / ``stream_text`` / ``cancel_generation`` API is
kept for callers (WritingService, Evaluation, Memory, Adapter Evaluation).
Since Phase 3 the bridge routes requests through ``ModelGatewayService`` with
the default ``LocalRuntimeProvider``, which in turn calls the existing runtime
via the private ``_*_impl`` methods below.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from llm_studio.api import errors as api_errors
from llm_studio.generation import CancellationToken
from llm_studio.model_gateway import (
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_INVALID_REQUEST,
    MODEL_GATEWAY_STREAM_FAILED,
    GenerateRequest,
    ModelGatewayError,
    ModelGatewayService,
)
from llm_studio.model_gateway.local_provider import LocalRuntimeProvider
from llm_studio.security.redaction import redact_sensitive_text

from .entities import RuntimeTextResult
from .errors import WritingRuntimeError


def _next_chunk(iterator):
    try:
        return True, next(iterator)
    except StopIteration:
        return False, None


def _error_code(exc: Exception) -> str | None:
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict):
        error = detail.get("error")
        if isinstance(error, dict):
            return str(error.get("code") or "") or None
    return getattr(exc, "code", None)


class WritingRuntimeBridge:
    """Reuse the app's runner resolver, inference gate, and GPU scheduler."""

    def __init__(
        self,
        *,
        resolve_runner: Callable[[str, str], Any],
        inference_scope: Callable[[str], AbstractAsyncContextManager],
        adapter_repository: Any | None = None,
        model_gateway: ModelGatewayService | None = None,
    ):
        self._resolve_runner = resolve_runner
        self._inference_scope = inference_scope
        self._adapter_repository = adapter_repository
        self._cancellations: dict[str, CancellationToken] = {}
        self.model_gateway = model_gateway or self._build_default_gateway()

    def _build_default_gateway(self) -> ModelGatewayService:
        gateway = ModelGatewayService()
        gateway.register_provider(LocalRuntimeProvider(runtime_bridge=self))
        return gateway

    def _build_request(
        self,
        *,
        generation_id: str,
        model_id: str,
        prompt: str,
        generation_params: dict[str, Any],
        adapter_id: str | None,
        stream: bool,
    ) -> GenerateRequest:
        return GenerateRequest(
            profile_id=None,
            provider="local_runtime",
            model=model_id,
            prompt=prompt,
            system_prompt=None,
            messages=[],
            generation_params=generation_params or {},
            adapter_id=adapter_id,
            stream=stream,
            task_type="novel_writing",
            privacy_level="local",
            metadata={
                "source": "writing_runtime_bridge",
                "generation_id": generation_id,
            },
        )

    async def generate_text(
        self,
        *,
        generation_id: str,
        model_id: str,
        prompt: str,
        generation_params: dict[str, Any],
        adapter_id: str | None = None,
    ) -> RuntimeTextResult:
        request = self._build_request(
            generation_id=generation_id,
            model_id=model_id,
            prompt=prompt,
            generation_params=generation_params,
            adapter_id=adapter_id,
            stream=False,
        )
        try:
            result = await self.model_gateway.generate(request)
        except ModelGatewayError as exc:
            raise self._map_gateway_error(exc, stream=False) from exc
        return RuntimeTextResult(
            text=result.text,
            finish_reason=result.finish_reason or "stop",
            latency_ms=result.latency_ms,
        )

    async def stream_text(
        self,
        *,
        generation_id: str,
        model_id: str,
        prompt: str,
        generation_params: dict[str, Any],
        adapter_id: str | None = None,
    ) -> AsyncIterator[str]:
        request = self._build_request(
            generation_id=generation_id,
            model_id=model_id,
            prompt=prompt,
            generation_params=generation_params,
            adapter_id=adapter_id,
            stream=True,
        )
        try:
            async for chunk in self.model_gateway.stream_generate(request):
                if chunk.event == "error":
                    continue
                if chunk.event == "done":
                    break
                if chunk.delta:
                    yield chunk.delta
        except ModelGatewayError as exc:
            raise self._map_gateway_error(exc, stream=True) from exc

    def cancel_generation(self, generation_id: str) -> bool:
        token = self._cancellations.get(generation_id)
        if token is None:
            return False
        token.cancel()
        return True

    async def _generate_text_impl(
        self,
        *,
        generation_id: str,
        model_id: str,
        prompt: str,
        generation_params: dict[str, Any],
        adapter_id: str | None = None,
    ) -> RuntimeTextResult:
        started = time.monotonic()
        resolved_model_id, runner = await self._runner(
            model_id,
            adapter_id,
            generation_id,
        )
        try:
            async with self._inference_scope(generation_id):
                text = await asyncio.to_thread(
                    runner.generate,
                    prompt,
                    **self._runner_params(generation_params),
                )
        except WritingRuntimeError:
            raise
        except Exception as exc:
            message = redact_sensitive_text(str(exc)) or "本地模型生成失败。"
            raise WritingRuntimeError(
                api_errors.WRITING_GENERATION_FAILED,
                message,
            ) from exc
        return RuntimeTextResult(
            text=str(text),
            finish_reason="stop",
            latency_ms=int((time.monotonic() - started) * 1000),
        )

    async def _stream_text_impl(
        self,
        *,
        generation_id: str,
        model_id: str,
        prompt: str,
        generation_params: dict[str, Any],
        adapter_id: str | None = None,
    ) -> AsyncIterator[str]:
        _, runner = await self._runner(model_id, adapter_id, generation_id)
        cancellation = CancellationToken()
        self._cancellations[generation_id] = cancellation
        try:
            async with self._inference_scope(generation_id):
                iterator = iter(
                    runner.generate_stream(
                        prompt,
                        cancellation_token=cancellation,
                        **self._runner_params(generation_params),
                    )
                )
                while True:
                    has_chunk, chunk = await asyncio.to_thread(_next_chunk, iterator)
                    if not has_chunk:
                        break
                    if chunk:
                        yield str(chunk)
        except WritingRuntimeError:
            raise
        except Exception as exc:
            if cancellation.is_cancelled:
                return
            message = redact_sensitive_text(str(exc)) or "本地模型流式生成失败。"
            raise WritingRuntimeError(
                api_errors.WRITING_STREAM_FAILED,
                message,
            ) from exc
        finally:
            self._cancellations.pop(generation_id, None)

    async def _runner(
        self,
        model_id: str,
        adapter_id: str | None,
        owner: str,
    ):
        try:
            resolved_model_id, runner = await self._resolve_runner(model_id, owner)
        except Exception as exc:
            code = _error_code(exc)
            mapped = (
                api_errors.WRITING_MODEL_NOT_FOUND
                if code == api_errors.MODEL_NOT_FOUND
                else api_errors.WRITING_MODEL_NOT_LOADED
            )
            raise WritingRuntimeError(mapped, "指定模型不存在或无法加载。") from exc
        if adapter_id:
            if self._adapter_repository is None:
                raise WritingRuntimeError(
                    api_errors.WRITING_ADAPTER_NOT_FOUND,
                    "未找到指定 Adapter。",
                )
            try:
                adapter = self._adapter_repository.get(adapter_id)
                loaded = set(runner.list_loaded_adapters())
                if adapter.name not in loaded:
                    await asyncio.to_thread(
                        runner.load_adapter,
                        adapter,
                        adapter.name,
                    )
                await asyncio.to_thread(runner.activate_adapter, adapter.name)
            except Exception as exc:
                raise WritingRuntimeError(
                    api_errors.WRITING_ADAPTER_NOT_FOUND,
                    "指定 Adapter 不存在或无法加载。",
                ) from exc
        else:
            try:
                await asyncio.to_thread(runner.deactivate_adapter)
            except Exception:
                pass
        return resolved_model_id, runner

    @staticmethod
    def _runner_params(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "temperature": params["temperature"],
            "top_p": params["top_p"],
            "max_tokens": params["max_tokens"],
            "repetition_penalty": params["repetition_penalty"],
            "stop": params.get("stop") or [],
        }

    def _map_gateway_error(
        self,
        exc: ModelGatewayError,
        *,
        stream: bool,
    ) -> WritingRuntimeError:
        original_code = (exc.details or {}).get("original_code")
        if original_code in {
            api_errors.WRITING_MODEL_NOT_FOUND,
            api_errors.WRITING_MODEL_NOT_LOADED,
            api_errors.WRITING_MODEL_NOT_SUPPORTED,
            api_errors.WRITING_ADAPTER_NOT_FOUND,
        }:
            return WritingRuntimeError(str(original_code), exc.message)
        if exc.code == LOCAL_RUNTIME_UNAVAILABLE:
            return WritingRuntimeError(
                api_errors.WRITING_MODEL_NOT_LOADED,
                exc.message,
            )
        if exc.code == MODEL_GATEWAY_INVALID_REQUEST:
            return WritingRuntimeError(
                api_errors.WRITING_INVALID_GENERATION_PARAMS,
                exc.message,
            )
        if stream or exc.code == MODEL_GATEWAY_STREAM_FAILED:
            return WritingRuntimeError(api_errors.WRITING_STREAM_FAILED, exc.message)
        if exc.code == MODEL_GATEWAY_GENERATION_FAILED:
            return WritingRuntimeError(
                api_errors.WRITING_GENERATION_FAILED,
                exc.message,
            )
        return WritingRuntimeError(api_errors.WRITING_GENERATION_FAILED, exc.message)
