import asyncio

import pytest

from llm_studio.model_gateway import (
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    MODEL_PROFILE_DISABLED,
    MODEL_PROFILE_NOT_FOUND,
    GenerateRequest,
    GenerateResult,
    ModelGatewayError,
    ModelGatewayService,
)
from llm_studio.model_gateway.fake_provider import FakeProvider
from llm_studio.model_gateway.profile_service import ModelProfileService
from llm_studio.model_gateway.profiles import ModelProfileCreate


def _profile_service(tmp_path, **extra) -> ModelProfileService:
    service = ModelProfileService(tmp_path / "gateway.sqlite")
    service.create_profile(
        ModelProfileCreate(
            name=extra.pop("name", "Fake Profile"),
            provider=extra.pop("provider", "fake"),
            model=extra.pop("model", "fake"),
            default_params=extra.pop(
                "default_params", {"temperature": 0.3, "max_tokens": 256}
            ),
            **extra,
        )
    )
    return service


class _RecordingFakeProvider(FakeProvider):
    def __init__(self):
        super().__init__()
        self.last_request: GenerateRequest | None = None

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        self.last_request = request
        return await super().generate(request)


def test_profile_id_resolves_fake_provider(tmp_path):
    service = _profile_service(tmp_path)
    profile = service.list_profiles()[0]
    gateway = ModelGatewayService(profile_service=service)

    result = asyncio.run(
        gateway.generate(
            GenerateRequest(
                profile_id=profile.id,
                prompt="写正文",
                generation_params={},
            )
        )
    )

    assert isinstance(result, GenerateResult)
    assert result.provider == "fake"
    assert result.text


def test_profile_default_params_are_merged(tmp_path):
    service = _profile_service(tmp_path)
    profile = service.list_profiles()[0]
    provider = _RecordingFakeProvider()
    gateway = ModelGatewayService(providers={"fake": provider}, profile_service=service)

    result = asyncio.run(
        gateway.generate(
            GenerateRequest(profile_id=profile.id, prompt="写正文", generation_params={})
        )
    )

    assert result.text == "这是一段测试生成内容。"
    assert provider.last_request is not None
    assert provider.last_request.generation_params == {
        "temperature": 0.3,
        "max_tokens": 256,
    }


def test_request_params_override_profile_defaults(tmp_path):
    service = _profile_service(tmp_path)
    profile = service.list_profiles()[0]
    provider = _RecordingFakeProvider()
    gateway = ModelGatewayService(providers={"fake": provider}, profile_service=service)

    result = asyncio.run(
        gateway.generate(
            GenerateRequest(
                profile_id=profile.id,
                prompt="写正文",
                generation_params={"fake_text": "来自请求"},
            )
        )
    )

    assert result.text == "来自请求"
    assert provider.last_request is not None
    assert provider.last_request.generation_params["temperature"] == 0.3
    assert provider.last_request.generation_params["fake_text"] == "来自请求"


def test_disabled_profile_cannot_be_called(tmp_path):
    service = _profile_service(tmp_path, status="disabled")
    profile = service.list_profiles(status="disabled")[0]
    gateway = ModelGatewayService(profile_service=service)

    with pytest.raises(ModelGatewayError) as exc_info:
        asyncio.run(
            gateway.generate(
                GenerateRequest(profile_id=profile.id, prompt="写正文")
            )
        )

    assert exc_info.value.code == MODEL_PROFILE_DISABLED


def test_missing_profile_raises_not_found(tmp_path):
    service = _profile_service(tmp_path)
    gateway = ModelGatewayService(profile_service=service)

    with pytest.raises(ModelGatewayError) as exc_info:
        asyncio.run(
            gateway.generate(
                GenerateRequest(profile_id="missing", prompt="写正文")
            )
        )

    assert exc_info.value.code == MODEL_PROFILE_NOT_FOUND


def test_profile_provider_not_registered_raises(tmp_path):
    service = _profile_service(tmp_path, provider="local_runtime", model="m")
    profile = service.list_profiles()[0]
    gateway = ModelGatewayService(
        providers={},
        profile_service=service,
    )

    with pytest.raises(ModelGatewayError) as exc_info:
        asyncio.run(
            gateway.generate(
                GenerateRequest(profile_id=profile.id, prompt="写正文")
            )
        )

    assert exc_info.value.code == MODEL_GATEWAY_PROVIDER_NOT_FOUND
