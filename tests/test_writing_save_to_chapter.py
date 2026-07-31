import asyncio

import pytest

from llm_studio.writing.errors import WritingSaveTargetError
from tests.test_writing_service import _seed


def test_save_generation_only_updates_draft_or_summary(tmp_path):
    novels, _, _, writing, _, _, chapter, _, request = _seed(tmp_path)
    result = asyncio.run(writing.generate(request))

    saved = writing.save_output_to_chapter(
        result["generation_id"],
        target="draft_content",
    )
    assert saved["draft_content"] == result["text"]
    assert saved["final_content"] in {None, ""}
    assert saved["word_count"] > 0

    appended = writing.save_output_to_chapter(
        result["generation_id"],
        target="draft_content",
        append=True,
    )
    assert appended["draft_content"].count(result["text"]) == 2

    summary = writing.save_output_to_chapter(
        result["generation_id"],
        target="summary",
    )
    assert summary["summary"] == result["text"]
    assert novels.get_chapter(chapter["id"])["final_content"] in {None, ""}

    with pytest.raises(WritingSaveTargetError):
        writing.save_output_to_chapter(
            result["generation_id"],
            target="final_content",
        )
