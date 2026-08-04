import json

from llm_studio.model_gateway import (
    MODEL_GATEWAY_PROVIDER_NOT_FOUND,
    ModelGatewayError,
)


def test_error_code_is_preserved():
    error = ModelGatewayError(
        MODEL_GATEWAY_PROVIDER_NOT_FOUND,
        "Provider missing.",
        {"provider": "missing"},
    )

    assert error.code == MODEL_GATEWAY_PROVIDER_NOT_FOUND
    assert error.message == "Provider missing."
    assert error.details == {"provider": "missing"}


def test_error_details_are_json_serializable():
    error = ModelGatewayError(
        "MODEL_GATEWAY_ERROR",
        "Bad payload.",
        {"nested": {"value": 1}, "raw": object(), "tags": ["a", 2]},
    )

    payload = json.loads(error.to_json())

    assert payload["code"] == "MODEL_GATEWAY_ERROR"
    assert payload["details"]["nested"] == {"value": 1}
    assert isinstance(payload["details"]["raw"], str)


def test_error_str_contains_code_and_message():
    error = ModelGatewayError("MODEL_GATEWAY_ERROR", "Something failed.")

    text = str(error)

    assert "MODEL_GATEWAY_ERROR" in text
    assert "Something failed." in text
