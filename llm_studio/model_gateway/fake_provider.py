"""FakeProvider for tests and local development."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .errors import FAKE_PROVIDER_ERROR, ModelGatewayError
from .provider_base import BaseModelProvider
from .schemas import GenerateRequest, GenerateResult, StreamChunk

DEFAULT_FAKE_TEXT = "这是一段测试生成内容。"


class FakeProvider(BaseModelProvider):
    """Deterministic in-memory provider; never touches the network or runtime."""

    provider_name = "fake"

    def __init__(self, default_text: str = DEFAULT_FAKE_TEXT):
        self.default_text = default_text

    def generate(self, request: GenerateRequest) -> GenerateResult:
        params = request.generation_params or {}
        self._raise_if_error(params)
        text = self._resolve_text(request, params)
        return GenerateResult(
            text=text,
            finish_reason=str(params.get("fake_finish_reason") or "stop"),
            provider=self.provider_name,
            model=request.model,
            profile_id=request.profile_id,
            input_tokens=params.get("fake_input_tokens"),
            output_tokens=params.get("fake_output_tokens"),
            latency_ms=self._latency(params),
            raw_usage={
                "fake": True,
                "input_tokens": params.get("fake_input_tokens"),
                "output_tokens": params.get("fake_output_tokens"),
            },
        )

    def stream_generate(self, request: GenerateRequest) -> Iterator[StreamChunk]:
        params = request.generation_params or {}
        self._raise_if_error(params)
        text = self._resolve_text(request, params)
        for char in text:
            yield StreamChunk(
                delta=char,
                event="delta",
                provider=self.provider_name,
                model=request.model,
            )
        yield StreamChunk(
            delta="",
            event="done",
            provider=self.provider_name,
            model=request.model,
            finish_reason=str(params.get("fake_finish_reason") or "stop"),
        )

    def get_capabilities(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "streaming": True,
            "supports_adapter": False,
            "usage": False,
        }

    def health_check(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "ok"}

    def _resolve_text(self, request: GenerateRequest, params: dict[str, Any]) -> str:
        if params.get("fake_text"):
            return str(params["fake_text"])
        if params.get("fake_echo"):
            return request.prompt
        return self.default_text

    @staticmethod
    def _latency(params: dict[str, Any]) -> int | None:
        value = params.get("fake_latency_ms")
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _raise_if_error(params: dict[str, Any]) -> None:
        code = params.get("fake_error_code")
        if not code:
            return
        raise ModelGatewayError(
            str(code) or FAKE_PROVIDER_ERROR,
            f"FakeProvider failure: {code}",
            {"provider": "fake", "fake_error_code": code},
        )
