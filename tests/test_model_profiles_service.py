import pytest

from llm_studio.model_gateway import (
    MODEL_PROFILE_INVALID_PROVIDER,
    ModelGatewayError,
)
from llm_studio.model_gateway.profile_service import ModelProfileService
from llm_studio.model_gateway.profiles import ModelProfileCreate


def _service(tmp_path) -> ModelProfileService:
    return ModelProfileService(tmp_path / "gateway.sqlite")


def test_ensure_builtin_profiles_creates_both(tmp_path):
    service = _service(tmp_path)

    summary = service.ensure_builtin_profiles()

    assert summary == {"created": 2, "skipped": 0, "user_modified": 0}
    names = {profile.name for profile in service.list_profiles()}
    assert names == {"Fake Test Model", "Local Runtime Default"}
    assert service.get_default_profile() is not None
    assert service.get_default_profile().provider == "local_runtime"


def test_ensure_builtin_profiles_is_idempotent(tmp_path):
    service = _service(tmp_path)
    service.ensure_builtin_profiles()

    second = service.ensure_builtin_profiles()

    assert second == {"created": 0, "skipped": 2, "user_modified": 0}
    assert len(service.list_profiles()) == 2


def test_ensure_builtin_does_not_override_user_default(tmp_path):
    service = _service(tmp_path)
    user = service.create_profile(
        ModelProfileCreate(
            name="User Default",
            provider="local_runtime",
            model="user-model",
            is_default=True,
        )
    )

    service.ensure_builtin_profiles()

    assert service.get_default_profile().id == user.id


def test_create_profile_rejects_invalid_provider(tmp_path):
    service = _service(tmp_path)

    with pytest.raises(ModelGatewayError) as exc_info:
        service.create_profile(
            ModelProfileCreate(name="Bad", provider="unknown_provider")
        )

    assert exc_info.value.code == MODEL_PROFILE_INVALID_PROVIDER


def test_reserved_providers_cannot_be_enabled(tmp_path):
    service = _service(tmp_path)

    for provider in ("openai_compatible", "deepseek"):
        with pytest.raises(ModelGatewayError) as exc_info:
            service.create_profile(
                ModelProfileCreate(name="Future", provider=provider, status="enabled")
            )
        assert exc_info.value.code == MODEL_PROFILE_INVALID_PROVIDER
