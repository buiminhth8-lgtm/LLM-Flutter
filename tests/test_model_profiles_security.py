import pytest

from llm_studio.model_gateway import (
    MODEL_PROFILE_SECRET_NOT_ALLOWED,
    ModelGatewayError,
)
from llm_studio.model_gateway.profile_service import ModelProfileService
from llm_studio.model_gateway.profiles import ModelProfileCreate
from tests.test_novel_projects_api import _client


def _create_body(**connection):
    return {
        "name": "Secure",
        "provider": "local_runtime",
        "model": "m",
        "connection": connection,
    }


@pytest.mark.parametrize(
    "key",
    ["api_key", "API_KEY", "token", "access_token", "Authorization", "bearer", "secret"],
)
def test_connection_rejects_sensitive_keys(tmp_path, key):
    service = ModelProfileService(tmp_path / "gateway.sqlite")

    with pytest.raises(ModelGatewayError) as exc_info:
        service.create_profile(
            ModelProfileCreate(
                name="Secure",
                provider="local_runtime",
                model="m",
                connection={key: "sk-secret-value"},
            )
        )

    assert exc_info.value.code == MODEL_PROFILE_SECRET_NOT_ALLOWED
    assert "sk-secret-value" not in str(exc_info.value.details)


def test_api_response_does_not_expose_secrets(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    client.post(
        "/v1/model-profiles",
        json={
            "name": "Local",
            "provider": "local_runtime",
            "model": "m",
            "connection": {"label": "local-only"},
            "metadata": {"notes": "keep"},
        },
    )

    body = client.get("/v1/model-profiles").text

    assert "sk-secret" not in body
    assert "local-only" in body
