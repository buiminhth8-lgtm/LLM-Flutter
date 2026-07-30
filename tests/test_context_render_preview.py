from tests.test_context_api import create_context_fixture
from tests.test_novel_projects_api import _client
from tests.test_prompt_templates_api import _template_body


def test_context_render_preview_reuses_prompt_renderer(monkeypatch, tmp_path):
    client = _client(tmp_path, monkeypatch)
    fixture = create_context_fixture(client)
    template = client.post(
        "/v1/prompts/templates",
        json=_template_body(
            instruction_template=(
                "Title: {{project_title}}\n"
                "Chapter: {{chapter_title}}\n"
                "Goal: {{current_chapter_goal}}\n"
                "{{world_setting}}"
            )
        ),
    ).json()

    response = client.post(
        "/v1/context/render-preview",
        json={
            "project_id": fixture["project"]["id"],
            "chapter_id": fixture["chapter"]["id"],
            "template_id": template["id"],
            "user_variables": {"current_chapter_goal": "Meet the broker."},
            "save_record": False,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert "Stage 3 Novel" in result["rendered_prompt"]
    assert "Meet the broker." in result["rendered_prompt"]
    assert result["prompt_hash"]
    assert "generation" not in result
