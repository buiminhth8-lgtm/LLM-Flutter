"""Thin Hugging Face Hub client wrapper."""

from __future__ import annotations

import os
from pathlib import Path

from .entities import DownloadRequest
from .exceptions import DownloadError, UnauthorizedRepositoryError


class HuggingFaceDownloadClient:
    def snapshot_download(
        self,
        request: DownloadRequest,
        *,
        local_dir: Path,
        cache_dir: Path | None = None,
    ) -> Path:
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise DownloadError("未安装 huggingface_hub，请安装基础依赖。") from exc

        token = request.token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        try:
            result = snapshot_download(
                repo_id=request.repo_id,
                revision=request.revision,
                allow_patterns=list(request.allow_patterns) if request.allow_patterns else None,
                ignore_patterns=list(request.ignore_patterns) if request.ignore_patterns else None,
                local_dir=str(local_dir),
                cache_dir=str(cache_dir) if cache_dir else None,
                token=token,
                local_files_only=request.local_files_only,
            )
        except Exception as exc:
            text = str(exc)
            if "401" in text or "unauthorized" in text.lower() or "gated" in text.lower():
                raise UnauthorizedRepositoryError("私有或受限仓库未授权，请配置有效 Hugging Face Token。") from exc
            raise DownloadError(text) from exc
        return Path(result)
