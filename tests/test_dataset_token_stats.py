from __future__ import annotations

from llm_studio.datasets.token_stats import DatasetTokenStats, non_whitespace_char_count


def test_token_stats_are_stable_for_chinese_english_and_mixed_text():
    stats = DatasetTokenStats()
    assert non_whitespace_char_count(" 夜 色，A B ") == 5
    assert stats.estimate_text_tokens("夜色沉入旧城。") == 7
    assert stats.estimate_text_tokens("hello world") == 3
    sample = {
        "instruction": "写一段",
        "input": "black market",
        "output": "夜色沉入旧城。",
    }
    assert stats.sample_char_count(sample) == 21
    assert stats.estimate_sample_tokens(sample) == 13
