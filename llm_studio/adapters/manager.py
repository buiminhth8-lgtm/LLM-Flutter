"""Runtime LoRA adapter operations."""

from __future__ import annotations

from .entities import AdapterInfo
from .exceptions import AdapterCompatibilityError, AdapterError


class AdapterManager:
    def __init__(self, runner):
        self.runner = runner

    def load_adapter(self, adapter: AdapterInfo, adapter_name: str | None = None) -> str:
        if not adapter.compatible:
            raise AdapterCompatibilityError("; ".join(adapter.compatibility_errors))
        if self.runner.model is None:
            raise AdapterError("基础模型尚未加载。")
        name = adapter_name or adapter.name
        model = self.runner.model
        if not hasattr(model, "load_adapter"):
            raise AdapterError("当前模型或 PEFT 版本不支持动态加载 LoRA adapter。")
        model.load_adapter(str(adapter.path), adapter_name=name)
        return name

    def activate_adapter(self, adapter_name: str) -> None:
        model = self.runner.model
        if model is None or not hasattr(model, "set_adapter"):
            raise AdapterError("当前模型不支持切换 adapter。")
        model.set_adapter(adapter_name)

    def deactivate_adapter(self) -> None:
        model = self.runner.model
        if model is None:
            return
        if hasattr(model, "disable_adapter"):
            model.disable_adapter()

    def unload_adapter(self, adapter_name: str) -> None:
        model = self.runner.model
        if model is None:
            return
        if hasattr(model, "delete_adapter"):
            model.delete_adapter(adapter_name)

    def list_loaded_adapters(self) -> tuple[str, ...]:
        model = self.runner.model
        if model is None:
            return ()
        peft_config = getattr(model, "peft_config", None)
        if isinstance(peft_config, dict):
            return tuple(peft_config.keys())
        return ()
