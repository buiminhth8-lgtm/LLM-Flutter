from __future__ import annotations

from llm_studio.datasets.sample_builder import DatasetSampleBuilder


def _revision(**extra):
    return {
        "revision_id": "rev-1",
        "project_id": "project-1",
        "chapter_id": "chapter-1",
        "generation_id": "gen-1",
        "original_text": "model original",
        "edited_text": "human edited",
        "original_hash": "oh",
        "edited_hash": "eh",
        "status": "approved",
        "accepted_for_dataset": True,
        "edit_tags": ["language_polish"],
        "user_score": 4,
        **extra,
    }


def test_build_sft_from_revision_uses_prompt_as_input_and_edited_output():
    draft = DatasetSampleBuilder().build_sft_from_revision(
        _revision(),
        generation={"prompt_rendered": "rendered prompt"},
        prompt_version={"instruction_template": "根据设定续写小说正文。\n{{project_title}}"},
    )

    assert draft.sample_type == "sft"
    assert draft.instruction == "根据设定续写小说正文。"
    assert draft.input == "rendered prompt"
    assert draft.output == "human edited"
    assert draft.source_hash
    assert draft.content_hash
    assert draft.quality_score == 4
    assert draft.metadata["revision_tags"] == ["language_polish"]


def test_build_preference_from_revision_is_reserved():
    draft = DatasetSampleBuilder().build_preference_from_revision(
        _revision(),
        generation={"prompt_rendered": "prompt"},
    )

    assert draft.sample_type == "preference"
    assert draft.input == "prompt"
    assert draft.chosen == "human edited"
    assert draft.rejected == "model original"
    assert draft.metadata["experimental"] is True
