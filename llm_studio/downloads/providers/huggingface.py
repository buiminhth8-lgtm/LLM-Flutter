"""Hugging Face download provider."""

from __future__ import annotations

import threading
from pathlib import Path

from llm_studio.downloads.entities import DownloadRequest
from llm_studio.downloads.huggingface_client import HuggingFaceDownloadClient
from llm_studio.downloads.progress import DownloadProgressTracker, RemoteFile


class HuggingFaceDownloadProvider:
    name = "huggingface"

    def __init__(self, config, client: HuggingFaceDownloadClient | None = None):
        self.config = config
        self.client = client or HuggingFaceDownloadClient()

    def _cache_dir(self) -> Path:
        from llm_studio.models.storage import layout_from_config

        layout = layout_from_config(self.config)
        downloads_cfg = self.config.get("downloads", {})
        providers_cfg = downloads_cfg.get("providers", {}) if isinstance(downloads_cfg, dict) else {}
        hf_cfg = providers_cfg.get("huggingface", {}) if isinstance(providers_cfg, dict) else {}
        legacy_cfg = self.config.get("huggingface", {})
        cache_dir = hf_cfg.get("cache_dir") or legacy_cfg.get("cache_dir") or (layout.temp_dir / "hf-cache")
        return Path(cache_dir)

    def resolve_files(self, request: DownloadRequest) -> list[RemoteFile]:
        list_files = getattr(self.client, "list_files", None)
        if callable(list_files):
            return list_files(request)
        return []

    def download_file(
        self,
        request: DownloadRequest,
        file: RemoteFile,
        *,
        local_dir: Path,
    ) -> Path:
        download_file = getattr(self.client, "download_file", None)
        if callable(download_file):
            return download_file(request, file, local_dir=local_dir, cache_dir=self._cache_dir())
        self.download_snapshot(request, local_dir, DownloadProgressTracker(()))
        return local_dir / file.path

    def download_snapshot(
        self,
        request: DownloadRequest,
        target_dir: Path,
        progress: DownloadProgressTracker,
        cancel_token: threading.Event | None = None,
    ) -> Path:
        return self.client.snapshot_download(
            request,
            local_dir=target_dir,
            cache_dir=self._cache_dir(),
        )
