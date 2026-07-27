"""Disk usage summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from llm_studio.models.storage import layout_from_config


@dataclass(frozen=True)
class DiskUsageItem:
    category: str
    path: Path
    size_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {"category": self.category, "path": str(self.path), "size_bytes": self.size_bytes}


def path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


def collect_disk_usage(config) -> list[DiskUsageItem]:
    layout = layout_from_config(config)
    hf_cache = Path(config.get("huggingface", {}).get("cache_dir", "./data/huggingface"))
    if not hf_cache.is_absolute():
        hf_cache = (config.config_path.parent / hf_cache).resolve()
    categories = {
        "models": layout.root_dir,
        "downloads": layout.temp_dir,
        "huggingface_cache": hf_cache,
        "adapters": layout.adapters_dir,
        "rag_index": Path(config.get("rag", {}).get("index_path", "./data/rag")),
        "benchmarks": layout.benchmarks_dir,
        "jobs": layout.jobs_dir,
        "diagnostics": layout.diagnostics_dir,
        "trash": layout.trash_dir,
    }
    return [DiskUsageItem(name, path, path_size(path)) for name, path in categories.items()]
