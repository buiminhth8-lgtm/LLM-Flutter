"""Thin Hugging Face Hub client wrapper."""

from __future__ import annotations

import os
from fnmatch import fnmatch
from pathlib import Path

from llm_studio.security.redaction import redact_sensitive_text

from .entities import DownloadRequest
from .exceptions import (
    DownloadError,
    DownloadLocalFilesNotFoundError,
    DownloadNetworkError,
    RepositoryNotFoundError,
    RevisionNotFoundError,
    UnauthorizedRepositoryError,
)
from .progress import RemoteFile


def _token_for(request: DownloadRequest) -> str | None:
    return request.token or os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_HUB_TOKEN")


def _matches_patterns(path: str, patterns: tuple[str, ...] | None, *, default: bool) -> bool:
    if not patterns:
        return default
    return any(fnmatch(path, pattern) for pattern in patterns)


def _filter_files(files: list[RemoteFile], request: DownloadRequest) -> list[RemoteFile]:
    filtered: list[RemoteFile] = []
    for item in files:
        if not _matches_patterns(item.path, request.allow_patterns, default=True):
            continue
        if _matches_patterns(item.path, request.ignore_patterns, default=False):
            continue
        filtered.append(item)
    return filtered


class HuggingFaceDownloadClient:
    def list_files(self, request: DownloadRequest) -> list[RemoteFile]:
        try:
            from huggingface_hub import HfApi
        except ImportError as exc:
            raise DownloadError("huggingface_hub 未安装，请安装 Web/下载依赖。") from exc

        token = _token_for(request)
        try:
            info = HfApi().model_info(
                request.repo_id,
                revision=request.revision,
                token=token,
                files_metadata=True,
            )
        except Exception as exc:
            raise self._map_hf_error(exc) from exc

        files: list[RemoteFile] = []
        for sibling in getattr(info, "siblings", []) or []:
            filename = getattr(sibling, "rfilename", None)
            if not filename:
                continue
            size = getattr(sibling, "size", None)
            files.append(RemoteFile(path=str(filename), size=int(size) if size is not None else None))
        return _filter_files(sorted(files, key=lambda item: item.path), request)

    def download_file(
        self,
        request: DownloadRequest,
        file: RemoteFile,
        *,
        local_dir: Path,
        cache_dir: Path | None = None,
    ) -> Path:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise DownloadError("huggingface_hub 未安装，请安装 Web/下载依赖。") from exc

        token = _token_for(request)
        try:
            result = hf_hub_download(
                repo_id=request.repo_id,
                filename=file.path,
                revision=request.revision,
                local_dir=str(local_dir),
                cache_dir=str(cache_dir) if cache_dir else None,
                token=token,
                local_files_only=request.local_files_only,
            )
        except Exception as exc:
            raise self._map_hf_error(exc) from exc
        return Path(result)

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
            raise DownloadError("huggingface_hub 未安装，请安装 Web/下载依赖。") from exc

        token = _token_for(request)
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
            raise self._map_hf_error(exc) from exc
        return Path(result)

    def _map_hf_error(self, exc: Exception) -> DownloadError:
        text = redact_sensitive_text(str(exc)) or ""
        lowered = text.lower()
        if "local_files_only" in lowered or ("cannot find" in lowered and "cache" in lowered):
            return DownloadLocalFilesNotFoundError("??????????????")
        if "401" in text or "unauthorized" in lowered or "gated" in lowered:
            return UnauthorizedRepositoryError("私有或受限仓库未授权，请配置有效 Hugging Face Token。")
        if "revision" in lowered and ("not found" in lowered or "404" in text):
            return RevisionNotFoundError("未找到指定 Hugging Face revision。")
        if "404" in text or "repository not found" in lowered:
            return RepositoryNotFoundError("未找到 Hugging Face 仓库。")
        if "connection" in lowered or "timeout" in lowered or "network" in lowered:
            return DownloadNetworkError("下载网络错误，请稍后重试。")
        return DownloadError(text)

