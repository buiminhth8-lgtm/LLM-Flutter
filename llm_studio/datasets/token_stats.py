"""Deterministic token and character estimates for dataset preparation."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[^\sA-Za-z0-9]")


@dataclass(frozen=True)
class DatasetStats:
    sample_count: int
    char_count: int
    token_estimate: int


def non_whitespace_char_count(text: str) -> int:
    return sum(1 for char in (text or "").strip() if not char.isspace())


class DatasetTokenStats:
    """Stage 7 estimate that does not load a tokenizer or model."""

    def estimate_text_tokens(self, text: str) -> int:
        ascii_words = 0
        other_tokens = 0
        for token in _TOKEN_RE.findall(text or ""):
            if token.isascii() and any(char.isalnum() for char in token):
                ascii_words += 1
            else:
                other_tokens += 1
        return int(math.ceil(ascii_words * 1.3 + other_tokens))

    def sample_text(self, sample: dict[str, Any]) -> str:
        parts = [
            sample.get("instruction") or "",
            sample.get("input") or "",
            sample.get("output") or "",
            sample.get("chosen") or "",
            sample.get("rejected") or "",
        ]
        return "\n".join(part for part in parts if part)

    def estimate_sample_tokens(self, sample: dict[str, Any]) -> int:
        return self.estimate_text_tokens(self.sample_text(sample))

    def sample_char_count(self, sample: dict[str, Any]) -> int:
        return non_whitespace_char_count(self.sample_text(sample))

    def summarize(self, samples: list[dict[str, Any]]) -> DatasetStats:
        return DatasetStats(
            sample_count=len(samples),
            char_count=sum(self.sample_char_count(sample) for sample in samples),
            token_estimate=sum(self.estimate_sample_tokens(sample) for sample in samples),
        )
