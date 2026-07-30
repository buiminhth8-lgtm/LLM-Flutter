"""Context budget validation and measurement."""

from __future__ import annotations

from typing import Any

from .entities import ContextBudget
from .errors import ContextInvalidBudgetError
from .estimators import TokenEstimator


def normalize_budget(value: ContextBudget | dict[str, Any] | None) -> ContextBudget:
    if isinstance(value, ContextBudget):
        budget = value
    else:
        data = value or {}
        budget = ContextBudget(
            max_tokens=int(data.get("max_tokens", 4096)),
            reserved_output_tokens=int(data.get("reserved_output_tokens", 1200)),
            max_context_tokens=int(data.get("max_context_tokens", 2500)),
            max_chars=int(data.get("max_chars", 12000)),
            hard_limit=bool(data.get("hard_limit", True)),
        )
    if budget.max_tokens <= 0:
        raise ContextInvalidBudgetError("max_tokens must be greater than zero.")
    if budget.reserved_output_tokens < 0:
        raise ContextInvalidBudgetError("reserved_output_tokens cannot be negative.")
    if budget.reserved_output_tokens >= budget.max_tokens:
        raise ContextInvalidBudgetError("reserved_output_tokens must be smaller than max_tokens.")
    if budget.max_context_tokens <= 0 or budget.max_chars <= 0:
        raise ContextInvalidBudgetError("max_context_tokens and max_chars must be greater than zero.")
    return budget


class ContextBudgetManager:
    def __init__(self, budget: ContextBudget, estimator: TokenEstimator | None = None):
        self.budget = budget
        self.estimator = estimator or TokenEstimator()

    def measure(self, variables: dict[str, Any]) -> tuple[int, int]:
        text = "\n".join(_stringify(value) for value in variables.values() if value not in (None, ""))
        return self.estimator.estimate(text), len(text)

    def exceeds(self, variables: dict[str, Any]) -> bool:
        tokens, chars = self.measure(variables)
        return tokens > self.budget.effective_context_tokens or chars > self.budget.max_chars


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple, set)):
        return "\n".join(_stringify(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(f"{key}: {_stringify(item)}" for key, item in value.items())
    return str(value)
