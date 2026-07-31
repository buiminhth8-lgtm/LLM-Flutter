import pytest

from llm_studio.writing.errors import WritingInvalidTargetLengthError
from llm_studio.writing.length_control import (
    apply_length_control,
    count_content_chars,
    normalize_target_length,
    suggest_max_tokens,
)


def test_chinese_character_count_ignores_whitespace_but_counts_punctuation():
    assert count_content_chars(" 你 好，\n世界！ ") == 6


def test_soft_and_hard_length_controls():
    soft = normalize_target_length(
        {"unit": "chars", "min": 2, "max": 3, "strategy": "soft"}
    )
    text, finish, warnings = apply_length_control("甲乙丙丁", soft)
    assert text == "甲乙丙丁"
    assert finish == "stop"
    assert warnings[0]["code"] == "WRITING_OUTPUT_ABOVE_TARGET"

    hard = normalize_target_length(
        {"unit": "chars", "min": 2, "max": 3, "strategy": "hard"}
    )
    text, finish, warnings = apply_length_control("甲 乙丙丁", hard)
    assert count_content_chars(text) == 3
    assert finish == "length"
    assert warnings == []


def test_target_length_validation_and_token_suggestion():
    with pytest.raises(WritingInvalidTargetLengthError):
        normalize_target_length({"unit": "words", "min": 1, "max": 2})
    with pytest.raises(WritingInvalidTargetLengthError):
        normalize_target_length({"unit": "chars", "min": 10, "max": 2})
    assert suggest_max_tokens(
        normalize_target_length({"unit": "chars", "min": 10, "max": 100})
    ) == 120
