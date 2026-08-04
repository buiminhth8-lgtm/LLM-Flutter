import asyncio

import pytest

from llm_studio.model_gateway import (
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_GENERATION_FAILED,
    GenerateRequest,
    GenerateResult,
    ModelGatewayError,
    StreamChunk,
)
from llm_studio.writing import WritingRuntimeBridge
from llm_studio.writing.entities import RuntimeTextResult
from llm_studio.writing.errors import WritingRuntimeError


class _NoopAsyncContext:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeRunner:
    def __init__(self, text: str = "runner 文本", stream_chunks=("流", "式")):
        self.text = text
        self.stream_chunks = stream_chunks

    def generate(self, prompt, **kwargs):
        return self.text

    def generate_stream(self, prompt, cancellation_token=None, **kwargs):
        yield from self.stream_chunks

    def list_loaded_adapters(self):
        return ()

    def deactivate_adapter(self):
        pass


class _FakeGateway:
    def __init__(self):
        self.generate_calls: list[GenerateRequest] = []
        self.stream_calls: list[GenerateRequest] = []
        self.result = GenerateResult(
            text="gateway 文本",
            finish_reason="stop",
            provider="local_runtime",
            latency_ms=7,
        )
        self.error: ModelGatewayError | None = None

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        self.generate_calls.append(request)
        if self.error:
            raise self.error
        return self.result

    async def stream_generate(self, request: GenerateRequest):
        self.stream_calls.append(request)
        if self.error:
            raise self.error
        for delta in ("流式", "文本"):
            yield StreamChunk(
                delta=delta,
                event="delta",
                provider="local_runtime",
                model=request.model,
            )
        yield StreamChunk(
            delta="",
            event="done",
            provider="local_runtime",
            finish_reason="stop",
        )


def _dummy_scope(owner):
    return _NoopAsyncContext()


def _bridge(gateway=None):
    async def _resolve(model_id, owner):
        return model_id, _FakeRunner()

    return WritingRuntimeBridge(
        resolve_runner=_resolve,
        inference_scope=_dummy_scope,
        model_gateway=gateway,
    )


def test_generate_text_routes_through_model_gateway():
    gateway = _FakeGateway()
    bridge = _bridge(gateway)

    result = asyncio.run(
        bridge.generate_text(
            generation_id="gen-1",
            model_id="model-1",
            prompt="写一段正文",
            generation_params={"max_tokens": 64, "temperature": 0.5},
            adapter_id="adapter-1",
        )
    )

    assert isinstance(result, RuntimeTextResult)
    assert result.text == "gateway 文本"
    assert result.finish_reason == "stop"
    assert result.latency_ms == 7
    request = gateway.generate_calls[0]
    assert request.provider == "local_runtime"
    assert request.model == "model-1"
    assert request.adapter_id == "adapter-1"
    assert request.generation_params == {"max_tokens": 64, "temperature": 0.5}
    assert request.prompt == "写一段正文"
    assert request.stream is False
    assert request.task_type == "novel_writing"


def test_stream_text_routes_through_model_gateway():
    gateway = _FakeGateway()
    bridge = _bridge(gateway)

    async def _collect():
        return [
            chunk
            async for chunk in bridge.stream_text(
                generation_id="gen-2",
                model_id="model-2",
                prompt="续写正文",
                generation_params={"max_tokens": 128},
                adapter_id="adapter-2",
            )
        ]

    chunks = asyncio.run(_collect())

    assert chunks == ["流式", "文本"]
    request = gateway.stream_calls[0]
    assert request.provider == "local_runtime"
    assert request.model == "model-2"
    assert request.adapter_id == "adapter-2"
    assert request.stream is True


def test_default_gateway_registers_local_runtime_provider():
    bridge = _bridge()

    names = {item["name"] for item in bridge.model_gateway.list_providers()}

    assert "local_runtime" in names
    assert "fake" in names


def test_gateway_error_maps_back_to_writing_error_code():
    gateway = _FakeGateway()
    gateway.error = ModelGatewayError(
        MODEL_GATEWAY_GENERATION_FAILED,
        "local generation failed",
        {"original_code": "WRITING_MODEL_NOT_FOUND"},
    )
    bridge = _bridge(gateway)

    with pytest.raises(WritingRuntimeError) as exc_info:
        asyncio.run(
            bridge.generate_text(
                generation_id="gen-3",
                model_id="missing",
                prompt="正文",
                generation_params={},
            )
        )

    assert exc_info.value.code == "WRITING_MODEL_NOT_FOUND"


def test_local_runtime_unavailable_maps_to_model_not_loaded():
    gateway = _FakeGateway()
    gateway.error = ModelGatewayError(
        LOCAL_RUNTIME_UNAVAILABLE,
        "Local runtime is not configured.",
    )
    bridge = _bridge(gateway)

    with pytest.raises(WritingRuntimeError) as exc_info:
        asyncio.run(
            bridge.generate_text(
                generation_id="gen-4",
                model_id="model-1",
                prompt="正文",
                generation_params={},
            )
        )

    assert exc_info.value.code == "WRITING_MODEL_NOT_LOADED"


def test_full_chain_default_gateway_through_local_runtime_provider():
    bridge = _bridge()

    result = asyncio.run(
        bridge.generate_text(
            generation_id="gen-5",
            model_id="model-1",
            prompt="写一段正文",
            generation_params={
                "temperature": 0.8,
                "top_p": 0.9,
                "max_tokens": 64,
                "repetition_penalty": 1.1,
            },
        )
    )

    assert result.text == "runner 文本"
    assert result.latency_ms is not None

    async def _collect():
        return [
            chunk
            async for chunk in bridge.stream_text(
                generation_id="gen-6",
                model_id="model-1",
                prompt="续写正文",
                generation_params={
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 64,
                    "repetition_penalty": 1.1,
                },
            )
        ]

    chunks = asyncio.run(_collect())
    assert chunks == ["流", "式"]
