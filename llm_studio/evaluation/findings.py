"""Finding validation helpers."""

from __future__ import annotations

from .entities import FINDING_CATEGORIES, FINDING_SEVERITIES, FINDING_STATUSES
from .errors import EvaluationInvalidEvaluatorError


def validate_finding_status(status: str) -> str:
    value = str(status)
    if value not in FINDING_STATUSES:
        raise EvaluationInvalidEvaluatorError(f"Invalid finding status: {value}")
    return value


def safe_severity(value: str) -> str:
    return value if value in FINDING_SEVERITIES else "info"


def safe_category(value: str) -> str:
    return value if value in FINDING_CATEGORIES else "manual"
