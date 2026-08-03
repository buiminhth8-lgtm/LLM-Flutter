"""Manual scoring validation for Adapter Evaluation."""

from __future__ import annotations

from typing import Any

from .errors import AdapterEvalInvalidScoreError, AdapterEvalInvalidWinnerError

WINNERS = frozenset({"base", "adapter", "tie", "none"})
SCORE_DIMENSIONS = {
    "style": "文风贴合",
    "character_consistency": "人物一致性",
    "plot_coherence": "剧情连贯性",
    "worldbuilding": "世界观一致性",
    "dialogue": "对白质量",
    "language_quality": "语言质量",
    "detail_richness": "细节丰富度",
    "pacing": "节奏控制",
    "novelty": "新鲜感",
    "overall": "整体质量",
}


def validate_score(value: int | None, field: str) -> int | None:
    if value is None:
        return None
    try:
        score = int(value)
    except (TypeError, ValueError) as exc:
        raise AdapterEvalInvalidScoreError(f"{field} must be an integer.") from exc
    if score < 1 or score > 5:
        raise AdapterEvalInvalidScoreError(f"{field} must be between 1 and 5.")
    return score


def validate_winner(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    winner = str(value)
    if winner not in WINNERS:
        raise AdapterEvalInvalidWinnerError(f"Unsupported winner: {winner}")
    return winner


def suggest_winner(base_score: int | None, adapter_score: int | None) -> str | None:
    if base_score is None or adapter_score is None:
        return None
    if adapter_score > base_score:
        return "adapter"
    if base_score > adapter_score:
        return "base"
    return "tie"


def validate_dimensions(value: Any) -> dict[str, dict[str, int | None]]:
    if not value:
        return {}
    if not isinstance(value, dict):
        raise AdapterEvalInvalidScoreError("dimensions must be an object.")
    normalized: dict[str, dict[str, int | None]] = {}
    for name, scores in value.items():
        if name not in SCORE_DIMENSIONS:
            raise AdapterEvalInvalidScoreError(f"Unknown score dimension: {name}")
        if not isinstance(scores, dict):
            raise AdapterEvalInvalidScoreError(f"{name} scores must be an object.")
        normalized[name] = {
            "base": validate_score(scores.get("base"), f"{name}.base"),
            "adapter": validate_score(scores.get("adapter"), f"{name}.adapter"),
        }
    return normalized
