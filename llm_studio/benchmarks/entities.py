"""Benchmark entities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class BenchmarkConfig:
    model_id: str
    adapter_id: str | None = None
    prompt_set: str = "default"
    warmup_runs: int = 1
    measured_runs: int = 3
    max_new_tokens: int = 128
    context_lengths: tuple[int, ...] = (512, 2048)
    seed: int = 42


@dataclass(frozen=True)
class BenchmarkRun:
    input_tokens: int
    output_tokens: int
    load_time_seconds: float | None
    tokenizer_load_time_seconds: float | None
    ttft_seconds: float | None
    generation_seconds: float
    tokens_per_second: float | None
    peak_cuda_allocated_bytes: int | None
    peak_cuda_reserved_bytes: int | None
    process_memory_peak_bytes: int | None
    error: str | None = None


@dataclass(frozen=True)
class BenchmarkResult:
    id: str
    created_at: datetime
    config: BenchmarkConfig
    environment: dict[str, Any]
    runs: tuple[BenchmarkRun, ...]

    @classmethod
    def now(cls, result_id: str, config: BenchmarkConfig, environment: dict[str, Any], runs: list[BenchmarkRun]) -> BenchmarkResult:
        return cls(result_id, datetime.now(timezone.utc), config, environment, tuple(runs))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "config": self.config.__dict__,
            "environment": self.environment,
            "runs": [run.__dict__ for run in self.runs],
            "summary": summarize_runs(self.runs),
        }


def summarize_runs(runs: tuple[BenchmarkRun, ...]) -> dict[str, float | None]:
    tps = sorted(run.tokens_per_second for run in runs if run.tokens_per_second is not None)
    ttft = sorted(run.ttft_seconds for run in runs if run.ttft_seconds is not None)

    def avg(values):
        return sum(values) / len(values) if values else None

    def median(values):
        if not values:
            return None
        mid = len(values) // 2
        if len(values) % 2:
            return values[mid]
        return (values[mid - 1] + values[mid]) / 2

    return {
        "tokens_per_second_avg": avg(tps),
        "tokens_per_second_median": median(tps),
        "tokens_per_second_min": min(tps) if tps else None,
        "tokens_per_second_max": max(tps) if tps else None,
        "ttft_avg": avg(ttft),
        "ttft_median": median(ttft),
        "ttft_min": min(ttft) if ttft else None,
        "ttft_max": max(ttft) if ttft else None,
    }
