from tests.test_novel_projects_api import _client
from tests.test_prompt_templates_api import _template_body


def test_create_new_version_and_activate_old_version(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    template = client.post("/v1/prompts/templates", json=_template_body()).json()
    first_version = client.get(f"/v1/prompts/templates/{template['id']}/versions").json()["data"][0]

    second = client.post(
        f"/v1/prompts/templates/{template['id']}/versions",
        json={
            "instruction_template": "新版 {{project_title}}",
            "variables_schema": {"project_title": {"type": "string", "required": True}},
            "default_values": {},
            "change_note": "v2",
        },
    )
    assert second.status_code == 200
    assert second.json()["version"] == 2

    activated = client.post(
        f"/v1/prompts/templates/{template['id']}/versions/{first_version['id']}/activate"
    )
    assert activated.status_code == 200
    assert activated.json()["active_version_id"] == first_version["id"]
