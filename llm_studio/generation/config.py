"""Generation request and result models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationConfig:
    max_new_tokens: int = 512
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.05
    do_sample: bool = True
    max_context_tokens: int = 4096
    timeout_seconds: float = 300


@dataclass(frozen=True)
class GenerationResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
