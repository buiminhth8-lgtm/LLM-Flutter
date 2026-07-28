"""LoRA merge helpers."""

from __future__ import annotations

from pathlib import Path

from llm_studio.models.storage import sanitize_local_name

from .entities import AdapterInfo


def plan_lora_merge_output(root_dir: Path, base_model_name: str, adapter: AdapterInfo, output_name: str | None) -> Path:
    name = sanitize_local_name(output_name or f"{base_model_name}-{adapter.name}-merged")
    target = root_dir / "transformers" / name
    if target.exists():
        raise FileExistsError(f"合并输出目录已存在，拒绝覆盖: {target}")
    return target
