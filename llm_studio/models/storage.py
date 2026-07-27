"""Storage and path-safety helpers for managed models."""

from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from .exceptions import InvalidModelPathError

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


@dataclass(frozen=True)
class ModelStorageLayout:
    root_dir: Path
    temp_dir: Path
    metadata_cache: Path
    trash_dir: Path
    adapters_dir: Path
    benchmarks_dir: Path
    jobs_dir: Path
    diagnostics_dir: Path
    allow_external_paths: bool = True
    follow_symlinks: bool = False
    minimum_free_space_gb: int = 10

    def ensure(self) -> None:
        for path in (
            self.root_dir,
            self.root_dir / "transformers",
            self.root_dir / "gguf",
            self.root_dir / "gptq",
            self.root_dir / "awq",
            self.temp_dir,
            self.trash_dir,
            self.adapters_dir,
            self.benchmarks_dir,
            self.jobs_dir,
            self.diagnostics_dir,
            self.metadata_cache.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


def layout_from_config(config) -> ModelStorageLayout:
    model_cfg = config.get("models", {})
    storage_cfg = config.get("storage", {})
    base = config.config_path.parent

    def resolve(value: str) -> Path:
        path = Path(value)
        if not path.is_absolute():
            path = base / path
        return path.resolve()

    root = resolve(model_cfg.get("root_dir", "./data/models"))
    return ModelStorageLayout(
        root_dir=root,
        temp_dir=resolve(model_cfg.get("temp_dir", "./data/downloads")),
        metadata_cache=resolve(model_cfg.get("metadata_cache", "./data/model_index.json")),
        trash_dir=resolve(storage_cfg.get("trash_dir", "./data/trash/models")),
        adapters_dir=resolve(model_cfg.get("adapters_dir", "./data/adapters")),
        benchmarks_dir=resolve(storage_cfg.get("benchmarks_dir", "./data/benchmarks")),
        jobs_dir=resolve(storage_cfg.get("jobs_dir", "./data/jobs")),
        diagnostics_dir=resolve(storage_cfg.get("diagnostics_dir", "./data/diagnostics")),
        allow_external_paths=bool(model_cfg.get("allow_external_paths", True)),
        follow_symlinks=bool(model_cfg.get("follow_symlinks", False)),
        minimum_free_space_gb=int(model_cfg.get("minimum_free_space_gb", 10)),
    )


def sanitize_local_name(value: str) -> str:
    name = value.strip().replace("/", "-").replace("\\", "-")
    if not name or name in {".", ".."} or ".." in name:
        raise InvalidModelPathError("local_name 不能为空或包含 '..'。")
    if ":" in name:
        raise InvalidModelPathError("local_name 不能包含冒号。")
    if re.search(r'[<>:"/\\|?*\x00-\x1f]', name):
        raise InvalidModelPathError("local_name 包含 Windows 不允许的字符。")
    stem = name.split(".")[0].upper()
    if stem in WINDOWS_RESERVED_NAMES:
        raise InvalidModelPathError(f"local_name 不能使用 Windows 保留名称: {stem}")
    return name


def ensure_within(path: Path, root: Path) -> Path:
    resolved = path.expanduser().resolve()
    root_resolved = root.expanduser().resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise InvalidModelPathError(f"路径不在受管理目录内: {resolved}") from exc
    return resolved


def disk_free_bytes(path: Path) -> int:
    path.mkdir(parents=True, exist_ok=True)
    return shutil.disk_usage(path).free


def atomic_replace_directory(src: Path, dst: Path) -> None:
    if dst.exists():
        raise InvalidModelPathError(f"目标目录已存在，拒绝覆盖: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    os.replace(src, dst)
