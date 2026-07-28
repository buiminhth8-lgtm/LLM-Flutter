"""Benchmark metric helpers."""

from __future__ import annotations


def tokens_per_second(output_tokens: int, ttft_seconds: float | None, total_generation_seconds: float) -> float | None:
    if output_tokens <= 0:
        return None
    after_first = total_generation_seconds - (ttft_seconds or 0.0)
    if after_first <= 0:
        return None
    return output_tokens / after_first


def cuda_peak_memory() -> tuple[int | None, int | None]:
    try:
        import torch
    except Exception:
        return None, None
    if not torch.cuda.is_available():
        return None, None
    return torch.cuda.max_memory_allocated(), torch.cuda.max_memory_reserved()


def reset_cuda_peak_memory() -> None:
    try:
        import torch
    except Exception:
        return
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()


def sync_cuda() -> None:
    try:
        import torch
    except Exception:
        return
    if torch.cuda.is_available():
        torch.cuda.synchronize()
