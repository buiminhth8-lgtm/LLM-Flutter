"""Score normalization helpers for Evaluation Center."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .errors import EvaluationInvalidScoreError


def clamp_score(value: float, *, minimum: float = 1.0, maximum: float = 5.0) -> float:
    return max(minimum, min(maximum, float(value)))


def ratio_to_score(ratio: float, *, inverse: bool = False) -> float:
    value = 1.0 - ratio if inverse else ratio
    return clamp_score(1.0 + max(0.0, min(1.0, value)) * 4.0)


def validate_manual_score(value: Any, field: str = "overall_score") -> int | None:
    if value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise EvaluationInvalidScoreError(f"{field} must be between 1 and 5.") from exc
    if score < 1 or score > 5:
        raise EvaluationInvalidScoreError(f"{field} must be between 1 and 5.")
    return score


def validate_dimensions(dimensions: dict[str, Any]) -> dict[str, int]:
    clean: dict[str, int] = {}
    for key, value in (dimensions or {}).items():
        score = validate_manual_score(value, str(key))
        if score is not None:
            clean[str(key)] = score
    return clean


def aggregate_overall_score(metrics: Iterable[dict[str, Any]]) -> float | None:
    values: list[float] = []
    for metric in metrics:
        name = str(metric.get("metric_name") or "")
        value = metric.get("metric_value")
        if value is None:
            continue
        if name.endswith("_score") or name == "manual_overall_score":
            values.append(clamp_score(float(value)))
    if not values:
        return None
    return round(sum(values) / len(values), 2)

