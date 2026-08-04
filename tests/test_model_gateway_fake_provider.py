import pytest

from llm_studio.model_gateway import (
    FAKE_PROVIDER_ERROR,
    FakeProvider,
    GenerateRequest,
    ModelGatewayError,
    StreamChunk,
)


def _request(**params) -> GenerateRequest:
    return GenerateRequest(
        provider="fake",
        prompt="测试提示",
        generation_params=params,
    )


def test_fake_provider_returns_fake_text():
    provider = FakeProvider()

    result = provider.generate(_request(fake_text="这是一段测试生成内容。"))

    assert result.text == "这是一段测试生成内容。"
    assert result.provider == "fake"
    assert result.finish_reason == "stop"


def test_fake_provider_returns_custom_finish_reason():
    provider = FakeProvider()

    result = provider.generate(
        _request(fake_text="内容", fake_finish_reason="length")
    )

    assert result.finish_reason == "length"


def test_fake_provider_raises_configured_error():
    provider = FakeProvider()

    with pytest.raises(ModelGatewayError) as exc_info:
        provider.generate(_request(fake_error_code=FAKE_PROVIDER_ERROR))

    assert exc_info.value.code == FAKE_PROVIDER_ERROR


def test_fake_provider_streams_multiple_chunks():
    provider = FakeProvider()

    chunks = list(provider.stream_generate(_request(fake_text="你好世界")))

    assert len(chunks) > 1
    assert all(isinstance(chunk, StreamChunk) for chunk in chunks)
    assert "".join(chunk.delta for chunk in chunks if chunk.event == "delta") == "你好世界"


def test_fake_provider_stream_ends_with_done_and_finish_reason():
    provider = FakeProvider()

    chunks = list(provider.stream_generate(_request(fake_text="内容")))

    assert chunks[-1].event == "done"
    assert chunks[-1].finish_reason == "stop"
