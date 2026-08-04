import asyncio

import pytest

from llm_studio.model_gateway import (
    LOCAL_RUNTIME_UNAVAILABLE,
    MODEL_GATEWAY_GENERATION_FAILED,
    MODEL_GATEWAY_UNSUPPORTED_STREAMING,
    GenerateRequest,
    GenerateResult,
    LocalRuntimeProvider,
    ModelGatewayError,
)


class FakeRuntimeBridge:
    """Sync fake compatible with the project's bridge interface."""

    def __init__(self, text: str = "local generated text"):
        self.text = text
        self.calls: list[dict] = []
        self.error: Exception | None = None

    def generate_text(
        self,
        model_id,
        prompt,
        generation_params,
        adapter_id=None,
        generation_id=None,
    ):
        self.calls.append(
            {
                "model_id": model_id,
                "prompt": prompt,
                "generation_params": generation_params,
                "adapter_id": adapter_id,
                "generation_id": generation_id,
            }
        )
        if self.error:
            raise self.error
        from llm_studio.writing.entities import RuntimeTextResult

        return RuntimeTextResult(text=self.text, finish_reason="stop", latency_ms=3)

    def stream_text(self, model_id, prompt, generation_params, adapter_id=None, generation_id=None):
        yield from self.text


class AsyncFakeRuntimeBridge:
    async def generate_text(
        self,
        model_id,
        prompt,
        generation_params,
        adapter_id=None,
        generation_id=None,
    ):
        return "async generated text"


def _request(**params) -> GenerateRequest:
    return GenerateRequest(
        provider="local_runtime",
        model="model-1",
        prompt="写一段正文",
        adapter_id="adapter-1",
        generation_params=params,
    )


def test_local_provider_raises_when_runtime_missing():
    provider = LocalRuntimeProvider()

    with pytest.raises(ModelGatewayError) as exc_info:
        asyncio.run(provider.generate(_request()))

    assert exc_info.value.code == LOCAL_RUNTIME_UNAVAILABLE


def test_local_provider_generates_with_fake_bridge():
    bridge = FakeRuntimeBridge("生成的正文")
    provider = LocalRuntimeProvider(runtime_bridge=bridge)

    result = asyncio.run(provider.generate(_request()))

    assert isinstance(result, GenerateResult)
    assert result.text == "生成的正文"
    assert result.provider == "local_runtime"
    assert result.finish_reason == "stop"
    assert result.latency_ms == 3
    assert result.input_tokens is None
    assert result.output_tokens is None


def test_local_provider_forwards_model_adapter_and_params():
    bridge = FakeRuntimeBridge()
    provider = LocalRuntimeProvider(runtime_bridge=bridge)

    asyncio.run(provider.generate(_request(max_tokens=64, temperature=0.5)))

    call = bridge.calls[0]
    assert call["model_id"] == "model-1"
    assert call["adapter_id"] == "adapter-1"
    assert call["generation_params"] == {"max_tokens": 64, "temperature": 0.5}
    assert call["generation_id"]


def test_local_provider_converts_runtime_exception():
    bridge = FakeRuntimeBridge()
    bridge.error = RuntimeError("boom")
    provider = LocalRuntimeProvider(runtime_bridge=bridge)

    with pytest.raises(ModelGatewayError) as exc_info:
        asyncio.run(provider.generate(_request()))

    assert exc_info.value.code == MODEL_GATEWAY_GENERATION_FAILED
    assert exc_info.value.details["original_type"] == "RuntimeError"


def test_local_provider_supports_async_bridge_generate():
    provider = LocalRuntimeProvider(runtime_bridge=AsyncFakeRuntimeBridge())

    result = asyncio.run(provider.generate(_request()))

    assert result.text == "async generated text"


def test_local_provider_streams_with_sync_bridge():
    bridge = FakeRuntimeBridge("同步流")
    provider = LocalRuntimeProvider(runtime_bridge=bridge)

    async def _collect():
        return [chunk async for chunk in provider.stream_generate(_request())]

    chunks = asyncio.run(_collect())

    assert "".join(chunk.delta for chunk in chunks if chunk.event == "delta") == "同步流"
    assert chunks[-1].event == "done"
    assert chunks[-1].finish_reason == "stop"


def test_local_provider_raises_unsupported_streaming_for_async_bridge():
    provider = LocalRuntimeProvider(runtime_bridge=AsyncFakeRuntimeBridge())

    with pytest.raises(ModelGatewayError) as exc_info:
        async def _collect():
            return [chunk async for chunk in provider.stream_generate(_request())]

        asyncio.run(_collect())

    assert exc_info.value.code == MODEL_GATEWAY_UNSUPPORTED_STREAMING


def test_local_provider_health_check_reflects_configuration():
    assert LocalRuntimeProvider().health_check()["status"] == "unavailable"
    assert (
        LocalRuntimeProvider(runtime_bridge=FakeRuntimeBridge()).health_check()["status"]
        == "ok"
    )
