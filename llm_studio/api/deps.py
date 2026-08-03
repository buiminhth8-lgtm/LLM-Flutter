"""Shared API dependencies configured by the FastAPI app factory."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiState:
    config: Any | None = None
    download_manager: Any | None = None
    job_repository: Any | None = None
    job_queue: Any | None = None
    diagnostics_exporter: Any | None = None
    novel_service: Any | None = None
    prompt_service: Any | None = None
    context_service: Any | None = None
    writing_service: Any | None = None
    revision_service: Any | None = None
    dataset_service: Any | None = None
    finetune_service: Any | None = None
    adapter_evaluation_service: Any | None = None
    memory_service: Any | None = None
    evaluation_service: Any | None = None


_state = ApiState()


def configure_api_state(**kwargs: Any) -> None:
    for name, value in kwargs.items():
        if not hasattr(_state, name):
            raise AttributeError(f"Unknown API state dependency: {name}")
        setattr(_state, name, value)


def get_api_state() -> ApiState:
    return _state
