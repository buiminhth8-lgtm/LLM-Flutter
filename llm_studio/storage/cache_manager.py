"""Conservative cache cleanup helpers."""

from __future__ import annotations

import shutil
import time
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
