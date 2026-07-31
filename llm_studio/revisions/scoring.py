"""Revision user score validation and warnings."""

from __future__ import annotations

from typing import Any

from .errors import RevisionInvalidScoreError

SCORE_LABELS: dict[int, str] = {
    1: "很差，不建议训练",
    2: "较差，需要重写",
    3: "可用，但一般",
    4: "较好，适合候选样本",
    5: "很好，强烈建议进入训练候选",
}


def validate_user_score(score: Any) -> int | None:
    if score is None:
        return None
    try:
        value = int(score)
    except (TypeError, ValueError) as exc:
        raise RevisionInvalidScoreError("user_score must be an integer from 1 to 5.") from exc
    if value not in SCORE_LABELS:
        raise RevisionInvalidScoreError("user_score must be between 1 and 5.")
    return value


def dataset_candidate_warnings(
    *,
    accepted_for_dataset: bool,
    user_score: int | None,
) -> list[dict[str, str]]:
    if accepted_for_dataset and user_score is not None and user_score < 4:
        return [
            {
                "code": "REVISION_LOW_SCORE_DATASET_CANDIDATE",
                "message": "user_score is below 4; keep this only as a manually confirmed dataset candidate.",
            }
        ]
    return []
