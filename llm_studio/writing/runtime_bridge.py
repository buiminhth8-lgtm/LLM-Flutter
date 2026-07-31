"""Adapter between WritingService and the existing loaded-model runtime."""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from llm_studio.api import errors as api_errors
from llm_studio.generation import CancellationToken
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
    ):
        self._resolve_runner = resolve_runner
        self._inference_scope = inference_scope
        self._adapter_repository = adapter_repository
        self._cancellations: dict[str, CancellationToken] = {}

    async def _runner(self, model_id: str, adapter_id: str | None, owner: str):
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
                    await asyncio.to_thread(runner.load_adapter, adapter, adapter.name)
                await asyncio.to_thread(runner.activate_adapter, adapter.name)
            except Exception as exc:
                raise WritingRuntimeError(
                    api_errors.WRITING_ADAPTER_NOT_FOUND,
                    "指定 Adapter 不存在或无法加载。",
                ) from exc
        return resolved_model_id, runner

    async def generate_text(
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

    async def stream_text(
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
            raise WritingRuntimeError(api_errors.WRITING_STREAM_FAILED, message) from exc
        finally:
            self._cancellations.pop(generation_id, None)

    def cancel_generation(self, generation_id: str) -> bool:
        token = self._cancellations.get(generation_id)
        if token is None:
            return False
        token.cancel()
        return True

    @staticmethod
    def _runner_params(params: dict[str, Any]) -> dict[str, Any]:
        return {
            "temperature": params["temperature"],
            "top_p": params["top_p"],
            "max_tokens": params["max_tokens"],
            "repetition_penalty": params["repetition_penalty"],
            "stop": params.get("stop") or [],
        }
