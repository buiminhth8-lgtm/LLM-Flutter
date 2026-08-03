from llm_studio.prompts.defaults import (
    DEFAULT_PROMPT_TEMPLATES,
    builtin_content_hash,
)
from llm_studio.prompts.variables import extract_variables
from tests.test_novel_projects_api import _client


def _ensure(client):
    response = client.post("/v1/prompts/defaults/ensure")
    assert response.status_code == 200
    return response.json()["data"]


def _template_by_key(client, builtin_key: str) -> dict:
    items = client.get(
        "/v1/prompts/templates", params={"scope": "global", "limit": 200}
    ).json()["data"]
    for item in items:
        if (item.get("metadata") or {}).get("builtin_key") == builtin_key:
            return item
    raise AssertionError(f"builtin template not found: {builtin_key}")


def test_default_templates_are_idempotent(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)

    first = _ensure(client)
    second = _ensure(client)

    assert first["installed_count"] >= 24
    assert first["skipped_count"] == 0
    assert first["upgraded_count"] == 0
    assert first["user_modified_count"] == 0
    assert len(first["template_keys"]) >= 24
    assert "novel.chapter_generate.v2" in first["template_keys"]
    assert "novel.consistency_check.v2" in first["template_keys"]

    assert second["installed_count"] == 0
    assert second["skipped_count"] >= 24
    assert second["upgraded_count"] == 0
    assert second["user_modified_count"] == 0


def test_every_default_template_has_full_content(monkeypatch, tmp_path):
    _client(tmp_path, monkeypatch)
    assert len(DEFAULT_PROMPT_TEMPLATES) >= 24
    keys = [template["metadata"]["builtin_key"] for template in DEFAULT_PROMPT_TEMPLATES]
    assert len(keys) == len(set(keys))

    for template in DEFAULT_PROMPT_TEMPLATES:
        metadata = template["metadata"]
        assert metadata["builtin"] is True
        assert metadata["builtin_key"]
        assert metadata["language"] == "zh-CN"
        assert metadata["category"] in {"writing", "planning", "editing"}
        assert metadata["version"] == 2
        assert template["system_prompt"]
        assert template["role_prompt"]
        assert template["instruction_template"]
        assert template["output_constraints"]
        assert template["negative_prompt"]
        assert template["variables_schema"]
        assert template["default_values"]

        used = extract_variables(
            template["system_prompt"],
            template["role_prompt"],
            template["instruction_template"],
            template["output_constraints"],
            template["negative_prompt"],
        )
        undeclared = used - set(template["variables_schema"])
        assert not undeclared, f"{metadata['builtin_key']}: {undeclared}"


def test_user_modified_builtin_template_is_not_overwritten(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _ensure(client)

    template = _template_by_key(client, "novel.chapter_generate.v2")
    modified = client.post(
        f"/v1/prompts/templates/{template['id']}/versions",
        json={
            "instruction_template": "用户修改后的章节正文模板。",
            "variables_schema": template.get("variables_schema") or {},
            "default_values": template.get("default_values") or {},
            "change_note": "user edit",
        },
    )
    assert modified.status_code == 200

    result = _ensure(client)
    assert result["user_modified_count"] >= 1
    assert result["upgraded_count"] == 0

    after = client.get(f"/v1/prompts/templates/{template['id']}").json()
    assert after["active_version"]["instruction_template"] == "用户修改后的章节正文模板。"


def test_pristine_old_builtin_template_is_upgraded(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _ensure(client)

    builtin = next(
        template
        for template in DEFAULT_PROMPT_TEMPLATES
        if template["metadata"]["builtin_key"] == "novel.chapter_generate.v2"
    )
    old_body = {
        **builtin,
        "instruction_template": builtin["instruction_template"] + "（旧版）",
    }
    # Simulate an older pristine builtin installed with its own content hash.
    client.post(
        "/v1/prompts/templates",
        json={
            "name": "章节正文生成（旧版）",
            "type": old_body["type"],
            "scope": "global",
            "description": old_body["description"],
            "system_prompt": old_body["system_prompt"],
            "role_prompt": old_body["role_prompt"],
            "instruction_template": old_body["instruction_template"],
            "negative_prompt": old_body["negative_prompt"],
            "output_constraints": old_body["output_constraints"],
            "variables_schema": old_body["variables_schema"],
            "default_values": old_body["default_values"],
            "metadata": {
                "builtin": True,
                "builtin_key": "novel.chapter_generate.v2",
                "language": "zh-CN",
                "category": "writing",
                "recommended": True,
                "version": 1,
                "content_hash": builtin_content_hash(old_body),
            },
        },
    )

    result = _ensure(client)
    assert result["upgraded_count"] >= 1
    assert result["user_modified_count"] == 0

    upgraded = _template_by_key(client, "novel.chapter_generate.v2")
    detail = client.get(f"/v1/prompts/templates/{upgraded['id']}").json()
    assert "（旧版）" not in detail["active_version"]["instruction_template"]
    assert detail["active_version"]["change_note"] == (
        "Upgrade default template to novel.chapter_generate.v2"
    )
    assert (detail["metadata"] or {}).get("version") == 2


def test_default_templates_render(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _ensure(client)

    cases = {
        "novel.chapter_generate.v2": {
            "project_title": "长夜",
            "chapter_title": "第一章 黑市",
            "chapter_outline": "主角第一次进入黑市。",
        },
        "novel.chapter_continue.v2": {
            "project_title": "长夜",
            "draft_content": "他推开了那扇锈迹斑斑的铁门。",
            "current_chapter_goal": "发现黑市的秘密。",
        },
        "novel.consistency_check.v2": {
            "selected_text": "主角一剑劈开了城墙。",
            "characters": "主角：凡人剑客，无超凡力量。",
        },
    }
    for builtin_key, variables in cases.items():
        template = _template_by_key(client, builtin_key)
        rendered = client.post(
            "/v1/prompts/render",
            json={
                "template_id": template["id"],
                "variables": variables,
                "save_record": False,
            },
        )
        assert rendered.status_code == 200
        body = rendered.json()
        assert body["rendered_prompt"]
        assert body["missing_variables"] == []
        assert len(body["prompt_hash"]) == 64


def test_consistency_check_reports_missing_selected_text(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _ensure(client)

    template = _template_by_key(client, "novel.consistency_check.v2")
    rendered = client.post(
        "/v1/prompts/render",
        json={
            "template_id": template["id"],
            "variables": {},
            "save_record": False,
        },
    )
    assert rendered.status_code == 200
    body = rendered.json()
    assert "selected_text" in body["missing_variables"]


def test_copy_global_template_to_project(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    project = client.post("/v1/novels/projects", json={"title": "长夜"}).json()
    _ensure(client)
    template = _template_by_key(client, "novel.chapter_generate.v2")

    copied = client.post(
        f"/v1/prompts/templates/{template['id']}/copy-to-project",
        json={"project_id": project["id"], "name": "项目模板"},
    )

    assert copied.status_code == 200
    assert copied.json()["scope"] == "project"
    assert copied.json()["project_id"] == project["id"]


def test_copy_to_missing_project_returns_error(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    _ensure(client)
    template = _template_by_key(client, "novel.chapter_generate.v2")

    response = client.post(
        f"/v1/prompts/templates/{template['id']}/copy-to-project",
        json={"project_id": "missing"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROMPT_PROJECT_NOT_FOUND"
