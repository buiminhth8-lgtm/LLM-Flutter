import asyncio

from llm_studio.model_gateway import (
    MODEL_GATEWAY_INVALID_REQUEST,
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    FakeProvider,
    GenerateRequest,
    GenerateResult,
    LocalRuntimeProvider,
    ModelGatewayError,
    ModelGatewayService,
)


def _service() -> ModelGatewayService:
    return ModelGatewayService()


def test_service_registers_fake_provider_by_default():
    service = _service()

    names = {item["name"] for item in service.list_providers()}

    assert "fake" in names
    assert service.get_provider("fake").provider_name == "fake"


def test_service_can_register_local_runtime_provider():
    service = _service()

    service.register_provider(LocalRuntimeProvider())

    names = {item["name"] for item in service.list_providers()}
    assert "local_runtime" in names
    assert service.get_provider("local_runtime").provider_name == "local_runtime"


def test_service_raises_provider_not_found_for_unknown_provider():
    service = _service()

    try:
        asyncio.run(service.generate(GenerateRequest(provider="missing", prompt="正文")))
    except ModelGatewayError as exc:
        assert exc.code == MODEL_GATEWAY_PROVIDER_NOT_FOUND
        assert "missing" in exc.message
    else:
        raise AssertionError("expected MODEL_GATEWAY_PROVIDER_NOT_FOUND")


def test_service_rejects_empty_prompt():
    service = _service()

    try:
        asyncio.run(service.generate(GenerateRequest(provider="fake", prompt="   ")))
    except ModelGatewayError as exc:
        assert exc.code == MODEL_GATEWAY_INVALID_REQUEST
    else:
        raise AssertionError("expected MODEL_GATEWAY_INVALID_REQUEST")


def test_service_generate_returns_result_and_fills_latency():
    service = _service()

    result = asyncio.run(
        service.generate(
            GenerateRequest(
                provider="fake",
                prompt="写一段正文",
                generation_params={"fake_text": "生成内容"},
            )
        )
    )

    assert isinstance(result, GenerateResult)
    assert result.text == "生成内容"
    assert result.provider == "fake"
    assert result.latency_ms is not None
    assert result.latency_ms >= 0


def test_service_list_providers_includes_capabilities():
    service = _service()
    service.register_provider(FakeProvider())

    items = service.list_providers()
    fake = next(item for item in items if item["name"] == "fake")

    assert fake["capabilities"]["streaming"] is True
    assert fake["health"]["status"] == "ok"
