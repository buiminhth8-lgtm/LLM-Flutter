"""Internal entities and constants for Stage 11 Evaluation Center."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TARGET_TYPES = frozenset(
    {
        "chapter",
        "generation",
        "revision",
        "adapter_eval_session",
        "project",
        "memory_retrieval",
    }
)

RUN_STATUSES = frozenset(
    {"created", "queued", "running", "completed", "failed", "cancelled", "archived"}
)

EVALUATOR_TYPES = frozenset(
    {
        "repetition",
        "style_consistency",
        "character_consistency",
        "world_consistency",
        "plot_coherence",
        "pacing",
        "memory_usage",
        "foreshadowing",
        "local_model_judge",
        "manual_score",
    }
)

FINDING_SEVERITIES = frozenset({"info", "warning", "error", "critical"})
FINDING_CATEGORIES = frozenset(
    {"repetition", "style", "character", "world", "plot", "pacing", "memory", "foreshadowing", "manual"}
)
FINDING_STATUSES = frozenset({"open", "acknowledged", "resolved", "dismissed"})


@dataclass(frozen=True)
class EvaluationTarget:
    target_type: str
    target_id: str
    text: str
    project_id: str | None = None
    chapter_id: str | None = None
    generation_id: str | None = None
    revision_id: str | None = None
    adapter_eval_session_id: str | None = None
    memory_retrieval_id: str | None = None
    snapshot: dict[str, Any] = field(default_factory=dict)
    references: dict[str, Any] = field(default_factory=dict)

