"""Unified model selection for chat and loading."""

from __future__ import annotations

from pathlib import Path

from llm_studio.runtime.capabilities import RuntimeCapabilities

from .compatibility import assess_model_compatibility
from .entities import LocalModel, ModelStatus
from .exceptions import InvalidModelPathError
from .repository import LocalModelRepository


class ModelSelectionError(RuntimeError):
    """Raised when no repository model can satisfy a request."""


def select_model_for_chat(
    requested_model: str | None,
    repository: LocalModelRepository,
    runtime_capabilities: RuntimeCapabilities,
) -> LocalModel:
    """Resolve a chat model id through the unified local model repository."""
    requested = (requested_model or "auto").strip()
    models = repository.list_models(refresh=False)

    if requested and requested != "auto":
        try:
            model = repository.get(requested)
        except InvalidModelPathError as exc:
            if Path(requested).expanduser().exists():
                raise ModelSelectionError("模型路径需要先在模型页面注册后才能用于聊天。") from exc
            raise ModelSelectionError(f"模型不存在: {requested}") from exc
        _ensure_ready(model)
        return model

    ready = [model for model in models if model.status == ModelStatus.READY]
    if not ready:
        raise ModelSelectionError("没有可用模型，请先在模型页面扫描、下载或注册模型。")

    def score(model: LocalModel) -> tuple[int, int, int]:
        report = assess_model_compatibility(
            model,
            total_vram_bytes=runtime_capabilities.total_vram_bytes or 8 * 1024**3,
        )
        risk_score = {"safe": 3, "warning": 2, "high-risk": 1, "unsupported": 0}.get(
            report.risk_level,
            1,
        )
        supported = 1 if report.supported else 0
        updated = int(model.updated_at.timestamp()) if model.updated_at else 0
        return supported, risk_score, updated

    return max(ready, key=score)


def _ensure_ready(model: LocalModel) -> None:
    if model.status != ModelStatus.READY:
        raise ModelSelectionError(f"模型状态为 {model.status.value}，不能加载或聊天。")
