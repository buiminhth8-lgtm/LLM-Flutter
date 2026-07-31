"""Internal entities for Novel Studio writing generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RuntimeTextResult:
    text: str
    finish_reason: str = "stop"
    latency_ms: int | None = None


@dataclass(frozen=True)
class WritingGenerationResult:
    generation_id: str
    project_id: str
    chapter_id: str | None
    mode: str
    model_id: str
    adapter_id: str | None
    text: str
    finish_reason: str
    output_char_count: int
    input_token_estimate: int
    output_token_estimate: int
    warnings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "generation_id": self.generation_id,
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "mode": self.mode,
            "model_id": self.model_id,
            "adapter_id": self.adapter_id,
            "text": self.text,
            "finish_reason": self.finish_reason,
            "output_char_count": self.output_char_count,
            "input_token_estimate": self.input_token_estimate,
            "output_token_estimate": self.output_token_estimate,
            "warnings": self.warnings,
        }
