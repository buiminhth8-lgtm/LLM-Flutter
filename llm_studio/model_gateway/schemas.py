"""Model Gateway request / result / profile DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class GenerateRequest:
    """Provider-neutral model generation request."""

    provider: str = "fake"
    prompt: str = ""
    profile_id: str | None = None
    model: str | None = None
    system_prompt: str | None = None
    messages: list[dict[str, Any]] = field(default_factory=list)
    generation_params: dict[str, Any] = field(default_factory=dict)
    adapter_id: str | None = None
    stream: bool = False
    task_type: str | None = None
    privacy_level: str = "local"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerateResult:
    """Normalized generation result."""

    text: str = ""
    finish_reason: str | None = None
    provider: str = ""
    model: str | None = None
    profile_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: int | None = None
    warnings: list[dict[str, Any]] = field(default_factory=list)
    raw_usage: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StreamChunk:
    """One chunk of a streamed generation."""

    delta: str = ""
    event: str = "delta"
    provider: str = ""
    model: str | None = None
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ModelProfile:
    """In-memory model profile (no database in this phase)."""

    id: str
    name: str
    provider: str
    model: str | None = None
    default_params: dict[str, Any] = field(default_factory=dict)
    capabilities: dict[str, Any] = field(default_factory=dict)
    status: str = "ready"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "provider": self.provider,
            "model": self.model,
            "default_params": self.default_params,
            "capabilities": self.capabilities,
            "status": self.status,
            "metadata": self.metadata,
        }
