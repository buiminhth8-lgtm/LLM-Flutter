"""Evaluator abstraction for Stage 11 Evaluation Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class EvaluationInput:
    target_type: str
    target_id: str
    project_id: str | None
    chapter_id: str | None
    text: str
    context: dict[str, Any] = field(default_factory=dict)
    references: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationMetricDraft:
    metric_name: str
    metric_value: float | None = None
    metric_unit: str | None = None
    metric: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationFindingDraft:
    severity: str
    category: str
    title: str
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    suggestion: str | None = None


@dataclass(frozen=True)
class EvaluationResult:
    metrics: list[EvaluationMetricDraft] = field(default_factory=list)
    findings: list[EvaluationFindingDraft] = field(default_factory=list)
    summary: str | None = None


class Evaluator(Protocol):
    evaluator_type: str

    def evaluate(self, input: EvaluationInput) -> EvaluationResult:
        ...

