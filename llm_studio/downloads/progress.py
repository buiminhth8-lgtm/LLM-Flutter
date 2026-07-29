"""Download progress tracking helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import PurePosixPath

from .entities import DownloadProgress


@dataclass(frozen=True)
class RemoteFile:
    path: str
    size: int | None = None


def sanitize_remote_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    normalized = str(filename).replace("\\", "/")
    parts = [
        part
        for part in PurePosixPath(normalized).parts
        if part not in {"", ".", ".."} and ":" not in part
    ]
    if not parts:
        return None
    return "/".join(parts[-4:])


class DownloadProgressTracker:
    def __init__(self, files: list[RemoteFile] | tuple[RemoteFile, ...]):
        self.files = tuple(files)
        known_sizes = [item.size for item in self.files if item.size is not None]
        self.total_bytes = sum(known_sizes) if len(known_sizes) == len(self.files) and self.files else None
        self.total_files = len(self.files) if self.files else None
        self.downloaded_bytes = 0
        self.completed_files = 0
        self.current_file: str | None = None
        self._started_at = time.monotonic()
        self._last_observed_bytes = 0

    def start_file(self, filename: str) -> DownloadProgress:
        self.current_file = sanitize_remote_filename(filename)
        return self.snapshot()

    def complete_file(self, filename: str, *, size_bytes: int | None) -> DownloadProgress:
        self.current_file = sanitize_remote_filename(filename)
        if size_bytes is not None:
            self.downloaded_bytes += max(0, int(size_bytes))
        self.completed_files += 1
        self._last_observed_bytes = self.downloaded_bytes
        return self.snapshot()

    def observe_local_bytes(self, downloaded_bytes: int) -> DownloadProgress:
        self.downloaded_bytes = max(self.downloaded_bytes, int(downloaded_bytes))
        self._last_observed_bytes = self.downloaded_bytes
        return self.snapshot()

    def snapshot(self) -> DownloadProgress:
        elapsed = max(0.001, time.monotonic() - self._started_at)
        speed = self.downloaded_bytes / elapsed if self.downloaded_bytes > 0 else None
        eta = None
        if self.total_bytes is not None and speed and speed > 0:
            remaining = max(0, self.total_bytes - self.downloaded_bytes)
            eta = remaining / speed
        return DownloadProgress(
            downloaded_bytes=self.downloaded_bytes,
            total_bytes=self.total_bytes,
            completed_files=self.completed_files,
            total_files=self.total_files,
            speed_bytes_per_second=speed,
            eta_seconds=eta,
            current_file=self.current_file,
        )

