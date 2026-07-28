"""Conservative cache cleanup helpers."""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from llm_studio.models.storage import ensure_within, layout_from_config

from .cleanup_policy import CleanupPolicy


class CacheManager:
    def __init__(self, config):
        self.config = config
        self.layout = layout_from_config(config)
        self.policy = CleanupPolicy.from_config(config)

    def cleanup_incomplete_downloads(self) -> int:
        return self._remove_old_dirs(self.layout.temp_dir, self.policy.incomplete_download_days, prefix="job-")

    def cleanup_old_benchmarks(self) -> int:
        return self._remove_old_files(self.layout.benchmarks_dir, self.policy.benchmark_retention_days, suffixes={".json", ".md"})

    def preview_cleanup(self, categories: set[str] | None = None) -> list[CleanupPreviewItem]:
        selected = categories or {
            "downloads_failed",
            "uploads_temp",
            "benchmarks",
            "diagnostics",
            "trash",
        }
        items: list[CleanupPreviewItem] = []
        if "downloads_failed" in selected:
            items.extend(
                self._preview_old_dirs(
                    self.layout.temp_dir,
                    self.policy.incomplete_download_days,
                    category="downloads_failed",
                    prefix="job-",
                    reason="older_than_retention",
                )
            )
        if "benchmarks" in selected:
            items.extend(
                self._preview_old_files(
                    self.layout.benchmarks_dir,
                    self.policy.benchmark_retention_days,
                    category="benchmarks",
                    suffixes={".json", ".md"},
                    reason="older_than_retention",
                )
            )
        if "uploads_temp" in selected:
            upload_root = Path(self.config.get("uploads", {}).get("temp_dir", "./data/uploads"))
            if not upload_root.is_absolute():
                upload_root = (self.config.config_path.parent / upload_root).resolve()
            items.extend(
                self._preview_old_dirs(
                    upload_root,
                    0,
                    category="uploads_temp",
                    prefix="",
                    reason="temporary_upload",
                )
            )
            items.extend(
                self._preview_old_files(
                    upload_root,
                    0,
                    category="uploads_temp",
                    suffixes=None,
                    reason="temporary_upload",
                    recursive=False,
                )
            )
        if "diagnostics" in selected:
            items.extend(
                self._preview_old_files(
                    self.layout.diagnostics_dir,
                    0,
                    category="diagnostics",
                    suffixes={".zip"},
                    reason="diagnostic_package",
                )
            )
        if "trash" in selected:
            items.extend(
                self._preview_old_dirs(
                    self.layout.trash_dir,
                    self.policy.trash_retention_days,
                    category="trash",
                    prefix="",
                    reason="older_than_retention",
                )
            )
        return items

    def cleanup_preview_items(self, items: list[CleanupPreviewItem]) -> dict[str, object]:
        removed: list[dict[str, object]] = []
        errors: list[dict[str, object]] = []
        for item in items:
            path = Path(item.path)
            try:
                self._assert_cleanable_path(path, item.category)
                if path.is_dir():
                    shutil.rmtree(path)
                elif path.is_file():
                    path.unlink()
                removed.append(item.to_dict())
            except Exception as exc:
                errors.append({**item.to_dict(), "error": str(exc)})
        return {
            "removed": removed,
            "errors": errors,
            "removed_size_bytes": sum(int(item["size_bytes"]) for item in removed),
        }

    def empty_trash(self, *, confirm: bool = False) -> int:
        if not confirm:
            return 0
        return self._remove_old_dirs(self.layout.trash_dir, 0, prefix="")

    def _remove_old_dirs(self, root: Path, days: int, *, prefix: str) -> int:
        root.mkdir(parents=True, exist_ok=True)
        cutoff = time.time() - days * 86400
        removed = 0
        for item in root.iterdir():
            if prefix and not item.name.startswith(prefix):
                continue
            if item.is_dir() and item.stat().st_mtime <= cutoff:
                ensure_within(item, root)
                shutil.rmtree(item)
                removed += 1
        return removed

    def _remove_old_files(self, root: Path, days: int, *, suffixes: set[str]) -> int:
        if not root.exists():
            return 0
        cutoff = time.time() - days * 86400
        removed = 0
        for item in root.iterdir():
            if item.is_file() and item.suffix in suffixes and item.stat().st_mtime <= cutoff:
                ensure_within(item, root)
                item.unlink()
                removed += 1
        return removed

    def _preview_old_dirs(
        self,
        root: Path,
        days: int,
        *,
        category: str,
        prefix: str,
        reason: str,
    ) -> list[CleanupPreviewItem]:
        if not root.exists():
            return []
        cutoff = time.time() - days * 86400
        items: list[CleanupPreviewItem] = []
        for item in root.iterdir():
            if prefix and not item.name.startswith(prefix):
                continue
            if item.is_dir() and item.stat().st_mtime <= cutoff:
                self._assert_cleanable_path(item, category)
                items.append(CleanupPreviewItem(str(item), category, _path_size(item), reason))
        return items

    def _preview_old_files(
        self,
        root: Path,
        days: int,
        *,
        category: str,
        suffixes: set[str] | None,
        reason: str,
        recursive: bool = False,
    ) -> list[CleanupPreviewItem]:
        if not root.exists():
            return []
        cutoff = time.time() - days * 86400
        iterator = root.rglob("*") if recursive else root.iterdir()
        items: list[CleanupPreviewItem] = []
        for item in iterator:
            if item.is_file() and (suffixes is None or item.suffix in suffixes) and item.stat().st_mtime <= cutoff:
                self._assert_cleanable_path(item, category)
                items.append(CleanupPreviewItem(str(item), category, item.stat().st_size, reason))
        return items

    def _assert_cleanable_path(self, path: Path, category: str) -> None:
        allowed_roots = {
            "downloads_failed": self.layout.temp_dir,
            "benchmarks": self.layout.benchmarks_dir,
            "diagnostics": self.layout.diagnostics_dir,
            "trash": self.layout.trash_dir,
        }
        upload_root = Path(self.config.get("uploads", {}).get("temp_dir", "./data/uploads"))
        if not upload_root.is_absolute():
            upload_root = (self.config.config_path.parent / upload_root).resolve()
        allowed_roots["uploads_temp"] = upload_root
        root = allowed_roots.get(category)
        if root is None:
            raise ValueError(f"Category is not cleanable: {category}")
        ensure_within(path, root)


@dataclass(frozen=True)
class CleanupPreviewItem:
    path: str
    category: str
    size_bytes: int
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "category": self.category,
            "size_bytes": self.size_bytes,
            "reason": self.reason,
        }


def _path_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            try:
                total += item.stat().st_size
            except OSError:
                continue
    return total
