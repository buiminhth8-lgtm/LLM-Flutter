"""Internal entities for Novel Studio Stage 9 Adapter Evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AdapterVariantResult:
    variant: str
    model_id: str
    adapter_id: str | None
    output_text: str = ""
    status: str = "created"
    finish_reason: str | None = None
    output_hash: str | None = None
    output_char_count: int = 0
    output_token_estimate: int = 0
    latency_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "model_id": self.model_id,
            "adapter_id": self.adapter_id,
            "output_text": self.output_text,
            "status": self.status,
            "finish_reason": self.finish_reason,
            "output_hash": self.output_hash,
            "output_char_count": self.output_char_count,
            "output_token_estimate": self.output_token_estimate,
            "latency_ms": self.latency_ms,
            "error_code": self.error_code,
            "error_message": self.error_message,
        }


@dataclass(frozen=True)
class AdapterPairResult:
    base: AdapterVariantResult
    adapter: AdapterVariantResult

    def to_dict(self) -> dict[str, Any]:
        return {"base": self.base.to_dict(), "adapter": self.adapter.to_dict()}
