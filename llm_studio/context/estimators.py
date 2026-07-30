"""Deterministic token and character estimates without model dependencies."""

from __future__ import annotations

import math
import re

_CJK_PATTERN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
_WORD_PATTERN = re.compile(r"[A-Za-z0-9_]+")


class TokenEstimator:
    """Estimate tokens using stable language-aware heuristics.

    CJK characters count as 1.1 tokens, Latin words as 1.3 tokens, and
    remaining punctuation or whitespace as 0.25 tokens.
    """

    def estimate(self, text: str) -> int:
        if not text:
            return 0
        cjk = len(_CJK_PATTERN.findall(text))
        words = len(_WORD_PATTERN.findall(text))
        consumed = cjk + sum(len(item) for item in _WORD_PATTERN.findall(text))
        remainder = max(0, len(text) - consumed)
        return max(0, math.ceil(cjk * 1.1 + words * 1.3 + remainder * 0.25))


def estimate_chars(text: str) -> int:
    return len(text or "")
