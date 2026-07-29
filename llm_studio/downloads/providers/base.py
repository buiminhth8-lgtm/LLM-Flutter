"""Provider protocol for model downloads."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Protocol

from llm_studio.downloads.entities import DownloadRequest
from llm_studio.downloads.progress import DownloadProgressTracker, RemoteFile


class DownloadProvider(Protocol):
    name: str

    def resolve_files(self, request: DownloadRequest) -> list[RemoteFile]:
        ...

    def download_file(
        self,
        request: DownloadRequest,
        file: RemoteFile,
        *,
        local_dir: Path,
    ) -> Path:
        ...

    def download_snapshot(
        self,
        request: DownloadRequest,
        target_dir: Path,
        progress: DownloadProgressTracker,
        cancel_token: threading.Event | None = None,
    ) -> Path:
        ...
