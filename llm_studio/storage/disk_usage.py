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
    cleanable: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "cleanable": self.cleanable,
        }


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
    upload_root = Path(config.get("uploads", {}).get("temp_dir", "./data/uploads"))
    rag_index = Path(config.get("rag", {}).get("index_path", "./data/rag"))
    if not upload_root.is_absolute():
        upload_root = (config.config_path.parent / upload_root).resolve()
    if not rag_index.is_absolute():
        rag_index = (config.config_path.parent / rag_index).resolve()
    categories: list[tuple[str, Path, bool]] = [
        ("models", layout.root_dir, False),
        ("external_models", layout.metadata_cache, False),
        ("adapters", layout.adapters_dir, False),
        ("rag_indexes", rag_index, False),
        ("rag_documents", rag_index / "documents", False),
        ("downloads_active", layout.temp_dir, False),
        ("download_temp", layout.temp_dir, True),
        ("downloads_failed", layout.temp_dir, True),
        ("uploads_temp", upload_root, True),
        ("benchmarks", layout.benchmarks_dir, True),
        ("logs", config.config_path.parent / "logs", True),
        ("diagnostics", layout.diagnostics_dir, True),
        ("trash", layout.trash_dir, True),
        ("huggingface_cache_managed", hf_cache, True),
        ("huggingface_cache_global", Path.home() / ".cache" / "huggingface", False),
    ]
    return [DiskUsageItem(name, path, path_size(path), cleanable) for name, path, cleanable in categories]
