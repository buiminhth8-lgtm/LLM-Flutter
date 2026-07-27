"""Small helpers for runtime hardware formatting."""

from __future__ import annotations

import os


def bytes_to_gib(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value / (1024 ** 3):.1f} GiB"


def auto_cpu_threads() -> int:
    count = os.cpu_count() or 4
    return max(1, min(count - 1, 12))
