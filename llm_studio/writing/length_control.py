"""Chinese-focused target length validation and output handling."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llm_studio.context.estimators import TokenEstimator

from .errors import WritingInvalidTargetLengthError


@dataclass(frozen=True)
class TargetLength:
    unit: str = "chars"
    minimum: int = 1200
    maximum: int = 1800
    strategy: str = "soft"

    def to_dict(self) -> dict[str, Any]:
        return {
            "unit": self.unit,
            "min": self.minimum,
            "max": self.maximum,
            "strategy": self.strategy,
        }


def normalize_target_length(value: Any) -> TargetLength:
    data = value or {}
    if hasattr(data, "model_dump"):
        data = data.model_dump()
    elif hasattr(data, "dict"):
        data = data.dict()
    if not isinstance(data, dict):
        raise WritingInvalidTargetLengthError("target_length must be an object.")
    unit = str(data.get("unit") or "chars").lower()
    strategy = str(data.get("strategy") or "soft").lower()
    try:
        minimum = int(data.get("min", 1200))
        maximum = int(data.get("max", 1800))
    except (TypeError, ValueError) as exc:
        raise WritingInvalidTargetLengthError(
            "target_length min and max must be integers."
        ) from exc
    if unit not in {"chars", "tokens"}:
        raise WritingInvalidTargetLengthError("target_length unit must be chars or tokens.")
    if strategy not in {"soft", "hard"}:
        raise WritingInvalidTargetLengthError("target_length strategy must be soft or hard.")
    if minimum < 0 or maximum < 1 or minimum > maximum:
        raise WritingInvalidTargetLengthError(
            "target_length requires 0 <= min <= max."
        )
    return TargetLength(unit, minimum, maximum, strategy)


def count_content_chars(text: str) -> int:
    """Count non-whitespace characters; punctuation remains part of the prose."""

    return sum(1 for character in text.strip() if not character.isspace())


def _hard_truncate_chars(text: str, maximum: int) -> str:
    count = 0
    output: list[str] = []
    for character in text.strip():
        if not character.isspace():
            if count >= maximum:
                break
            count += 1
        output.append(character)
    return "".join(output).rstrip()


def apply_length_control(
    text: str,
    target: TargetLength,
    *,
    estimator: TokenEstimator | None = None,
) -> tuple[str, str, list[dict[str, Any]]]:
    estimator = estimator or TokenEstimator()
    measure = count_content_chars(text) if target.unit == "chars" else estimator.estimate(text)
    warnings: list[dict[str, Any]] = []
    finish_reason = "stop"
    output = text.strip()
    if measure < target.minimum:
        warnings.append(
            {
                "code": "WRITING_OUTPUT_BELOW_TARGET",
                "message": "生成内容低于目标长度，未自动补写。",
                "actual": measure,
                "minimum": target.minimum,
                "unit": target.unit,
            }
        )
    if measure > target.maximum:
        if target.strategy == "hard":
            if target.unit == "chars":
                output = _hard_truncate_chars(output, target.maximum)
            else:
                ratio = target.maximum / max(1, measure)
                output = output[: max(1, int(len(output) * ratio))].rstrip()
            finish_reason = "length"
        else:
            warnings.append(
                {
                    "code": "WRITING_OUTPUT_ABOVE_TARGET",
                    "message": "生成内容超过目标长度；soft 策略保留完整输出。",
                    "actual": measure,
                    "maximum": target.maximum,
                    "unit": target.unit,
                }
            )
    return output, finish_reason, warnings


def suggest_max_tokens(
    target: TargetLength,
    *,
    configured_max: int = 32768,
) -> int:
    if target.unit == "tokens":
        return max(1, min(target.maximum, configured_max))
    return max(1, min(int(target.maximum * 1.2), configured_max))
