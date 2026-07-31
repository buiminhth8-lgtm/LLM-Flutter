from llm_studio.api.deps import get_api_state
from llm_studio.writing.errors import WritingRuntimeError
from tests.test_novel_projects_api import _client
from tests.test_writing_service import FakeRuntimeBridge


def _seed_api(client):
    project = client.post(
        "/v1/novels/projects",
        json={"title": "Stage 4"},
    ).json()
    chapter = client.post(
        f"/v1/novels/projects/{project['id']}/chapters",
        json={"title": "Chapter", "outline": "Enter the market"},
    ).json()
    template = client.post(
        "/v1/prompts/templates",
        json={
            "name": "Generate",
            "type": "chapter_generate",
            "scope": "global",
            "instruction_template": "{{project_title}} {{chapter_outline}}",
            "variables_schema": {},
            "default_values": {},
        },
    ).json()
    return project, chapter, template


def test_writing_generate_list_get_and_save_api(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    get_api_state().writing_service.runtime_bridge = FakeRuntimeBridge("生成正文")
    project, chapter, template = _seed_api(client)
    response = client.post(
        "/v1/writing/generate",
        json={
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "model_id": "fake-model",
            "mode": "chapter_generate",
            "target_length": {
                "unit": "chars",
                "min": 1,
                "max": 100,
                "strategy": "soft",
            },
            "generation_params": {"max_tokens": 64},
        },
    )
    assert response.status_code == 200
    generation = response.json()

    listed = client.get(
        f"/v1/writing/generations?project_id={project['id']}"
    )
    assert listed.status_code == 200
    assert listed.json()["data"][0]["generation_id"] == generation["generation_id"]
    assert (
        client.get(
            f"/v1/writing/generations/{generation['generation_id']}"
        ).status_code
        == 200
    )

    saved = client.post(
        f"/v1/writing/generations/{generation['generation_id']}/save-to-chapter",
        json={"target": "draft_content", "append": False},
    )
    assert saved.status_code == 200
    assert saved.json()["chapter"]["draft_content"] == "生成正文"

    forbidden = client.post(
        f"/v1/writing/generations/{generation['generation_id']}/save-to-chapter",
        json={"target": "final_content", "append": False},
    )
    assert forbidden.status_code == 400
    assert forbidden.json()["error"]["code"] == "WRITING_SAVE_TARGET_NOT_ALLOWED"


def test_writing_api_returns_stable_validation_and_model_errors(
    monkeypatch,
    tmp_path,
):
    client = _client(tmp_path, monkeypatch)
    project, chapter, template = _seed_api(client)
    body = {
        "project_id": project["id"],
        "chapter_id": chapter["id"],
        "template_id": template["id"],
        "model_id": "missing-model",
        "mode": "unknown",
        "target_length": {
            "unit": "chars",
            "min": 1,
            "max": 100,
            "strategy": "soft",
        },
        "generation_params": {"max_tokens": 64},
    }
    invalid = client.post("/v1/writing/generate", json=body)
    assert invalid.status_code == 400
    assert invalid.json()["error"]["code"] == "WRITING_INVALID_MODE"

    get_api_state().writing_service.runtime_bridge = FakeRuntimeBridge()
    get_api_state().writing_service.runtime_bridge.error = WritingRuntimeError(
        "WRITING_MODEL_NOT_FOUND",
        "Model not found.",
    )
    body["mode"] = "chapter_generate"
    missing = client.post("/v1/writing/generate", json=body)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "WRITING_MODEL_NOT_FOUND"


def test_writing_stream_api_emits_sse_and_persists_output(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    get_api_state().writing_service.runtime_bridge = FakeRuntimeBridge()
    project, chapter, template = _seed_api(client)
    with client.stream(
        "POST",
        "/v1/writing/stream",
        json={
            "project_id": project["id"],
            "chapter_id": chapter["id"],
            "template_id": template["id"],
            "model_id": "fake-model",
            "mode": "chapter_generate",
            "target_length": {
                "unit": "chars",
                "min": 1,
                "max": 100,
                "strategy": "soft",
            },
            "generation_params": {"max_tokens": 64, "stream": True},
        },
    ) as response:
        body = response.read().decode("utf-8")

    assert response.status_code == 200
    assert '"type": "start"' in body
    assert '"type": "delta"' in body
    assert '"type": "done"' in body
    records = get_api_state().writing_service.list_generations(
        project_id=project["id"]
    )
    assert records[0]["status"] == "succeeded"
    assert records[0]["model_output"] == "夜色落在旧城。"
