"""SSE event helpers for writing generation."""

from __future__ import annotations

import json
from typing import Any


def writing_sse_event(payload: dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def split_at_stop(text: str, stop_sequences: list[str]) -> tuple[str, bool]:
    """Return text before the earliest configured stop sequence."""

    positions = [
        position
        for stop in stop_sequences
        if stop and (position := text.find(stop)) >= 0
    ]
    if not positions:
        return text, False
    return text[: min(positions)], True
