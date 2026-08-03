"""Stage 11 evaluator registry."""

from __future__ import annotations

from .character_consistency import CharacterConsistencyEvaluator
from .foreshadowing import ForeshadowingEvaluator
from .local_model_judge import LocalModelJudgeEvaluator
from .memory_usage import MemoryUsageEvaluator
from .pacing import PacingEvaluator
from .plot_coherence import PlotCoherenceEvaluator
from .repetition import RepetitionEvaluator
from .style_consistency import StyleConsistencyEvaluator
from .world_consistency import WorldConsistencyEvaluator

HEURISTIC_EVALUATORS = {
    "repetition": RepetitionEvaluator,
    "style_consistency": StyleConsistencyEvaluator,
    "character_consistency": CharacterConsistencyEvaluator,
    "world_consistency": WorldConsistencyEvaluator,
    "plot_coherence": PlotCoherenceEvaluator,
    "pacing": PacingEvaluator,
    "memory_usage": MemoryUsageEvaluator,
    "foreshadowing": ForeshadowingEvaluator,
}

__all__ = [
    "CharacterConsistencyEvaluator",
    "ForeshadowingEvaluator",
    "HEURISTIC_EVALUATORS",
    "LocalModelJudgeEvaluator",
    "MemoryUsageEvaluator",
    "PacingEvaluator",
    "PlotCoherenceEvaluator",
    "RepetitionEvaluator",
    "StyleConsistencyEvaluator",
    "WorldConsistencyEvaluator",
]
