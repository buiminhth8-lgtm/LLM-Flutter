"""Download progress tracking helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import PurePosixPath
from threading import RLock

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
        self._file_sizes = {
            sanitize_remote_filename(item.path) or item.path: int(item.size)
            for item in self.files
            if item.size is not None
        }
        self.total_bytes = self._known_total_bytes()
        self.total_files = len(self.files) if self.files else None
        self.downloaded_bytes = 0
        self.completed_files = 0
        self.current_file: str | None = None
        self._started_at = time.monotonic()
        self._last_observed_bytes = 0
        self._file_downloaded: dict[str, int] = {}
        self._completed_file_keys: set[str] = set()
        self._lock = RLock()

    def start_file(self, filename: str) -> DownloadProgress:
        with self._lock:
            self.current_file = sanitize_remote_filename(filename)
            return self._snapshot_unlocked()

    def complete_file(self, filename: str, *, size_bytes: int | None) -> DownloadProgress:
        with self._lock:
            key = self._file_key(filename)
            self.current_file = sanitize_remote_filename(filename)
            if size_bytes is not None:
                previous = self._file_downloaded.get(key, 0)
                observed = max(previous, int(size_bytes))
                self.downloaded_bytes += observed - previous
                self._file_downloaded[key] = observed
            if key not in self._completed_file_keys:
                self.completed_files += 1
                self._completed_file_keys.add(key)
            self._last_observed_bytes = self.downloaded_bytes
            return self._snapshot_unlocked()

    def update_file(
        self,
        filename: str | None,
        *,
        downloaded_delta: int = 0,
        total_bytes: int | None = None,
    ) -> DownloadProgress:
        with self._lock:
            key = self._file_key(filename)
            self.current_file = sanitize_remote_filename(filename)
            if total_bytes is not None and total_bytes > 0:
                self._set_file_size(key, int(total_bytes))
            delta = max(0, int(downloaded_delta or 0))
            if delta:
                previous = self._file_downloaded.get(key, 0)
                self._file_downloaded[key] = previous + delta
                self.downloaded_bytes += delta
                self._last_observed_bytes = self.downloaded_bytes
            return self._snapshot_unlocked()

    def finish_file(self, filename: str | None, *, total_bytes: int | None = None) -> DownloadProgress:
        with self._lock:
            key = self._file_key(filename)
            self.current_file = sanitize_remote_filename(filename)
            if total_bytes is not None and total_bytes > 0:
                self._set_file_size(key, int(total_bytes))
                previous = self._file_downloaded.get(key, 0)
                observed = max(previous, int(total_bytes))
                self.downloaded_bytes += observed - previous
                self._file_downloaded[key] = observed
            if key not in self._completed_file_keys:
                self.completed_files += 1
                self._completed_file_keys.add(key)
            self._last_observed_bytes = self.downloaded_bytes
            return self._snapshot_unlocked()

    def observe_local_bytes(self, downloaded_bytes: int) -> DownloadProgress:
        with self._lock:
            self.downloaded_bytes = max(self.downloaded_bytes, int(downloaded_bytes))
            self._last_observed_bytes = self.downloaded_bytes
            return self._snapshot_unlocked()

    def observe_local_state(self, *, downloaded_bytes: int, completed_files: int) -> DownloadProgress:
        with self._lock:
            self.downloaded_bytes = max(self.downloaded_bytes, int(downloaded_bytes))
            self.completed_files = max(self.completed_files, int(completed_files))
            self._last_observed_bytes = self.downloaded_bytes
            return self._snapshot_unlocked()

    def snapshot(self) -> DownloadProgress:
        with self._lock:
            return self._snapshot_unlocked()

    def _file_key(self, filename: str | None) -> str:
        return sanitize_remote_filename(filename) or str(filename or "unknown")

    def _set_file_size(self, key: str, size: int) -> None:
        if size > 0:
            self._file_sizes[key] = size
            self.total_bytes = self._known_total_bytes()

    def _known_total_bytes(self) -> int | None:
        if not self.files:
            return None
        file_keys = {sanitize_remote_filename(item.path) or item.path for item in self.files}
        if file_keys and all(key in self._file_sizes for key in file_keys):
            return sum(self._file_sizes[key] for key in file_keys)
        return None

    def _snapshot_unlocked(self) -> DownloadProgress:
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
