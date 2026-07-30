from tests.test_novel_projects_api import _client


def _template_body(**extra):
    return {
        "name": "章节生成模板",
        "type": "chapter_generate",
        "scope": "global",
        "instruction_template": "标题：{{project_title}}\n大纲：{{chapter_outline}}",
        "variables_schema": {
            "project_title": {"type": "string", "required": True},
            "chapter_outline": {"type": "string", "required": True},
        },
        "default_values": {},
        **extra,
    }


def test_create_template_creates_version_and_metadata_update_does_not(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    created = client.post("/v1/prompts/templates", json=_template_body())
    assert created.status_code == 200
    template = created.json()
    assert template["active_version_id"]

    versions = client.get(f"/v1/prompts/templates/{template['id']}/versions")
    assert len(versions.json()["data"]) == 1
    assert versions.json()["data"][0]["version"] == 1

    patched = client.patch(
        f"/v1/prompts/templates/{template['id']}",
        json={"description": "metadata only"},
    )
    assert patched.status_code == 200
    versions_after = client.get(f"/v1/prompts/templates/{template['id']}/versions")
    assert len(versions_after.json()["data"]) == 1


def test_unknown_prompt_type_returns_stable_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    response = client.post("/v1/prompts/templates", json=_template_body(type="bad"))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PROMPT_INVALID_TYPE"


def test_render_prompt_saves_record(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    template = client.post("/v1/prompts/templates", json=_template_body()).json()

    rendered = client.post(
        "/v1/prompts/render",
        json={
            "template_id": template["id"],
            "variables": {"project_title": "长夜", "chapter_outline": "进入黑市"},
            "save_record": True,
        },
    )

    assert rendered.status_code == 200
    body = rendered.json()
    assert "长夜" in body["rendered_prompt"]
    assert body["missing_variables"] == []
    assert body["render_id"]
    assert len(body["prompt_hash"]) == 64
