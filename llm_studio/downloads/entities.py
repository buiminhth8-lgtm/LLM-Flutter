"""Download request and progress entities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadRequest:
    repo_id: str
    revision: str | None = None
    allow_patterns: tuple[str, ...] | None = None
    ignore_patterns: tuple[str, ...] | None = None
    local_name: str | None = None
    token: str | None = None
    local_files_only: bool = False


@dataclass(frozen=True)
class DownloadProgress:
    downloaded_bytes: int
    total_bytes: int | None
    completed_files: int
    total_files: int | None
    speed_bytes_per_second: float | None
    eta_seconds: float | None
    current_file: str | None

    def as_fraction(self) -> float | None:
        if self.total_bytes and self.total_bytes > 0:
            return min(1.0, self.downloaded_bytes / self.total_bytes)
        if self.total_files and self.total_files > 0:
            return min(1.0, self.completed_files / self.total_files)
        return None
