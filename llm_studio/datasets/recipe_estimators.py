"""Simple deterministic estimators for Stage 7 training recipe previews."""

from __future__ import annotations

from typing import Any


def estimate_vram_gb(
    *,
    method: str,
    gpu_vram_gb: float | None,
    max_seq_length: int,
    lora_rank: int,
) -> float:
    base = 6.5 if method == "qlora" else 11.0
    seq_factor = max_seq_length / 4096
    rank_factor = lora_rank / 16
    estimate = base * (0.85 + 0.15 * seq_factor) * (0.9 + 0.1 * rank_factor)
    if gpu_vram_gb and method == "qlora":
        estimate = min(estimate, max(float(gpu_vram_gb) - 0.5, 1.0))
    return round(estimate, 2)


def estimate_train_time_minutes(
    *,
    token_estimate: int,
    epochs: int,
    method: str,
    hardware: dict[str, Any],
) -> int:
    gpu_vram = float(hardware.get("gpu_vram_gb") or 8)
    speed = 850 if method == "qlora" else 1200
    if gpu_vram < 12:
        speed *= 0.75
    minutes = (max(token_estimate, 1) * max(epochs, 1)) / max(speed, 1) / 60
    return max(1, round(minutes))
