import pytest

from llm_studio.prompts.renderer import PromptRenderer


def _version(**extra):
    return {
        "id": "version-1",
        "template_id": "template-1",
        "system_prompt": "系统：{{project_title}}",
        "role_prompt": None,
        "instruction_template": "章节：{{chapter_outline}} 长度：{{target_length}}",
        "output_constraints": None,
        "negative_prompt": None,
        "variables_schema": {
            "project_title": {"type": "string", "required": True},
            "chapter_outline": {"type": "string", "required": True},
            "target_length": {"type": "string", "required": False},
        },
        "default_values": {"target_length": "1000 字"},
        "renderer": "simple_mustache",
        **extra,
    }


def test_renderer_fills_defaults_and_hashes_prompt():
    result = PromptRenderer().render(
        _version(),
        {"chapter_outline": "进入黑市"},
        {"project_title": "长夜"},
    )

    assert "长夜" in result.rendered_prompt
    assert "1000 字" in result.rendered_prompt
    assert result.missing_variables == []
    assert len(result.prompt_hash) == 64


def test_renderer_reports_missing_required_variables():
    result = PromptRenderer().render(_version(), {}, {})

    assert result.missing_variables == ["chapter_outline", "project_title"]


def test_renderer_rejects_too_long_prompt():
    version = _version(instruction_template="{{project_title}}")
    with pytest.raises(Exception) as exc:
        PromptRenderer().render(version, {"project_title": "x" * 200_001}, {})

    assert exc.value.code == "PROMPT_RENDER_TOO_LONG"
