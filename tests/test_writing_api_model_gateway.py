import json

from llm_studio.api.deps import get_api_state
from llm_studio.model_gateway import (
    MODEL_GATEWAY_GENERATION_FAILED,
    GenerateRequest,
    GenerateResult,
    ModelGatewayError,
    StreamChunk,
)
from tests.test_novel_projects_api import _client


class _FakeGateway:
    def __init__(self, text: str = "网关生成正文"):
        self.text = text
        self.error: ModelGatewayError | None = None

    async def generate(self, request: GenerateRequest) -> GenerateResult:
        if self.error:
            raise self.error
        return GenerateResult(
            text=self.text,
            finish_reason="stop",
            provider="local_runtime",
            model=request.model,
            latency_ms=5,
        )

    async def stream_generate(self, request: GenerateRequest):
        if self.error:
            raise self.error
        for char in self.text:
            yield StreamChunk(
                delta=char,
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


def _install_gateway(client, gateway):
    get_api_state().writing_service.runtime_bridge.model_gateway = gateway


def _seed(client):
    project = client.post("/v1/novels/projects", json={"title": "长夜"}).json()
    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "黑市", "outline": "主角进入黑市。"},
    ).json()
    template = client.post(
        "/v1/prompts/templates",
        json={
            "name": "章节生成",
            "type": "chapter_generate",
            "scope": "global",
            "instruction_template": "{{project_title}}\n{{chapter_outline}}",
            "variables_schema": {},
            "default_values": {},
        },
    ).json()
    return project, chapter, template


def _request_body(project, chapter, template):
    return {
        "project_id": project["id"],
        "chapter_id": chapter["id"],
        "template_id": template["id"],
        "model_id": "model-1",
        "adapter_id": "adapter-1",
        "mode": "chapter_generate",
        "target_length": {
            "unit": "chars",
            "min": 1,
            "max": 100,
            "strategy": "soft",
        },
        "generation_params": {"max_tokens": 64},
    }


def test_writing_api_generate_through_model_gateway(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _install_gateway(client, _FakeGateway())
    project, chapter, template = _seed(client)

    response = client.post(
        "/v1/writing/generate",
        json=_request_body(project, chapter, template),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "网关生成正文"
    assert body["finish_reason"] == "stop"
    assert body["generation_id"]
    assert body["model_id"] == "model-1"
    assert body["adapter_id"] == "adapter-1"
    assert {
        "generation_id",
        "project_id",
        "chapter_id",
        "mode",
        "model_id",
        "adapter_id",
        "text",
        "finish_reason",
        "output_char_count",
        "input_token_estimate",
        "output_token_estimate",
        "warnings",
    }.issubset(body.keys())


def test_writing_api_gateway_error_maps_to_writing_code_without_traceback(
    monkeypatch,
    tmp_path,
):
    client = _client(tmp_path, monkeypatch)
    gateway = _FakeGateway()
    gateway.error = ModelGatewayError(
        MODEL_GATEWAY_GENERATION_FAILED,
        "local generation failed",
        {"original_code": "WRITING_MODEL_NOT_FOUND"},
    )
    _install_gateway(client, gateway)
    project, chapter, template = _seed(client)

    response = client.post(
        "/v1/writing/generate",
        json=_request_body(project, chapter, template),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WRITING_MODEL_NOT_FOUND"
    assert "Traceback" not in response.text


def test_writing_api_stream_through_model_gateway(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _install_gateway(client, _FakeGateway())
    project, chapter, template = _seed(client)

    with client.stream(
        "POST",
        "/v1/writing/stream",
        json=_request_body(project, chapter, template),
    ) as response:
        assert response.status_code == 200
        events = []
        for line in response.iter_lines():
            if line and line.startswith("data: "):
                events.append(json.loads(line[len("data: ") :]))

    deltas = [event["text"] for event in events if event["type"] == "delta"]
    assert "".join(deltas) == "网关生成正文"
    done = next(event for event in events if event["type"] == "done")
    assert done["finish_reason"] == "stop"
    assert events[-1]["type"] == "end"
