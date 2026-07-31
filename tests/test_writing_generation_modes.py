import pytest

from llm_studio.writing.errors import WritingInvalidModeError
from llm_studio.writing.generation_modes import GENERATION_MODES, mode_template_type
from llm_studio.writing.service import WritingService


def test_generation_modes_map_to_prompt_types():
    assert "chapter_generate" in GENERATION_MODES
    assert "chapter_continue" in GENERATION_MODES
    assert "summary_generate" in GENERATION_MODES
    assert mode_template_type("chapter_polish") == "chapter_polish"


def test_unknown_generation_mode_is_rejected():
    with pytest.raises(WritingInvalidModeError):
        WritingService._validate_mode("unknown")
