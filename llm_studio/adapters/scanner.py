"""LoRA adapter scanner."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .entities import AdapterInfo


class AdapterScanner:
    def __init__(self, adapters_dir: Path):
        self.adapters_dir = adapters_dir

    def scan(self) -> list[AdapterInfo]:
        if not self.adapters_dir.exists():
            return []
        adapters: list[AdapterInfo] = []
        for path in self.adapters_dir.iterdir():
            if path.is_dir() and (path / "adapter_config.json").exists():
                adapters.append(self.scan_one(path))
        return adapters

    def scan_one(self, path: Path, base_model_path: str | None = None) -> AdapterInfo:
        path = path.expanduser().resolve()
        errors: list[str] = []
        try:
            data = json.loads((path / "adapter_config.json").read_text(encoding="utf-8"))
        except Exception as exc:
            data = {}
            errors.append(f"adapter_config.json 读取失败: {exc}")
        if not (path / "adapter_model.safetensors").exists() and not (path / "adapter_model.bin").exists():
            errors.append("缺少 adapter_model.safetensors 或 adapter_model.bin。")

        target_modules = data.get("target_modules") or ()
        if isinstance(target_modules, str):
            target_modules = (target_modules,)
        elif isinstance(target_modules, list):
            target_modules = tuple(str(item) for item in target_modules)
        else:
            target_modules = ()

        base = data.get("base_model_name_or_path")
        if base_model_path and base and Path(str(base)).name not in Path(base_model_path).name:
            errors.append("适配器声明的 base_model_name_or_path 与当前基座模型可能不一致。")

        return AdapterInfo(
            id=self._adapter_id(path),
            name=path.name,
            path=path,
            base_model_name_or_path=str(base) if base else None,
            peft_type=str(data.get("peft_type")) if data.get("peft_type") else None,
            task_type=str(data.get("task_type")) if data.get("task_type") else None,
            rank=int(data["r"]) if data.get("r") is not None else None,
            alpha=float(data["lora_alpha"]) if data.get("lora_alpha") is not None else None,
            target_modules=target_modules,
            size_bytes=sum(item.stat().st_size for item in path.rglob("*") if item.is_file()),
            compatible=not errors,
            compatibility_errors=tuple(errors),
        )

    def _adapter_id(self, path: Path) -> str:
        digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
        safe = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in path.name)[:80]
        return f"{safe}-{digest}"
