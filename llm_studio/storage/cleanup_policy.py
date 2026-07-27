"""Cleanup policy dataclass."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CleanupPolicy:
    incomplete_download_days: int = 7
    benchmark_retention_days: int = 90
    trash_retention_days: int = 30
    logs_retention_days: int = 30
    enabled: bool = True

    @classmethod
    def from_config(cls, config) -> CleanupPolicy:
        data = config.get("storage", {}).get("cleanup", {})
        return cls(
            incomplete_download_days=int(data.get("incomplete_download_days", 7)),
            benchmark_retention_days=int(data.get("benchmark_retention_days", 90)),
            trash_retention_days=int(data.get("trash_retention_days", 30)),
            logs_retention_days=int(data.get("logs_retention_days", 30)),
            enabled=bool(data.get("enabled", True)),
        )
