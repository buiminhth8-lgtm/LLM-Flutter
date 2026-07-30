"""ModelScope / 魔塔社区 download provider."""

from __future__ import annotations

import inspect
import os
import threading
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from llm_studio.downloads.entities import DownloadRequest
from llm_studio.downloads.exceptions import (
    DownloadProviderNotInstalledError,
    ModelScopeAuthRequiredError,
    ModelScopeDownloadError,
    ModelScopeLocalFilesNotFoundError,
    ModelScopeNetworkError,
    ModelScopeRepoNotFoundError,
)
from llm_studio.downloads.progress import DownloadProgressTracker, RemoteFile
from llm_studio.models.storage import layout_from_config
from llm_studio.security.redaction import redact_sensitive_text


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


class ModelScopeDownloadProvider:
    name = "modelscope"

    def __init__(self, config, client: Any | None = None):
        self.config = config
        self.client = client

    def _provider_config(self) -> dict[str, Any]:
        downloads_cfg = self.config.get("downloads", {})
        providers_cfg = downloads_cfg.get("providers", {}) if isinstance(downloads_cfg, dict) else {}
        scoped = providers_cfg.get("modelscope", {}) if isinstance(providers_cfg, dict) else {}
        legacy = self.config.get("modelscope", {})
        return {**(legacy if isinstance(legacy, dict) else {}), **(scoped if isinstance(scoped, dict) else {})}

    def _cache_dir(self) -> Path:
        cfg = self._provider_config()
        layout = layout_from_config(self.config)
        raw = os.environ.get("MODELSCOPE_CACHE") or cfg.get("cache_dir") or (layout.temp_dir / "modelscope-cache")
        return Path(raw)

    def _endpoint(self) -> str | None:
        cfg = self._provider_config()
        return os.environ.get("MODELSCOPE_ENDPOINT") or cfg.get("endpoint")

    def _token(self) -> str | None:
        cfg = self._provider_config()
        return os.environ.get("MODELSCOPE_API_TOKEN") or cfg.get("token")

    def resolve_files(self, request: DownloadRequest) -> list[RemoteFile]:
        if request.local_files_only:
            return []
        if self.client is not None and hasattr(self.client, "list_files"):
            return _filter_files(list(self.client.list_files(request)), request)
        try:
            from modelscope_hub.api import HubApi
        except ImportError as exc:
            raise DownloadProviderNotInstalledError("modelscope-hub 未安装，请安装下载依赖。") from exc

        try:
            api = self._create_hub_api(HubApi)
            list_func = self._repo_file_list_func(api)
            raw_files = self._call_supported_kwargs(
                list_func,
                model_id=request.repo_id,
                repo_id=request.repo_id,
                repo_type="model",
                revision=request.revision or "master",
                recursive=True,
            )
        except Exception as exc:
            raise self._map_modelscope_error(exc) from exc

        files: list[RemoteFile] = []
        for item in raw_files or []:
            if isinstance(item, str):
                files.append(RemoteFile(path=item, size=None))
                continue
            path = (
                getattr(item, "path", None)
                or getattr(item, "file_path", None)
                or getattr(item, "name", None)
                or getattr(item, "Path", None)
            )
            size = getattr(item, "size", None) or getattr(item, "Size", None)
            if path:
                files.append(RemoteFile(path=str(path), size=int(size) if size is not None else None))
        return _filter_files(sorted(files, key=lambda item: item.path), request)

    def download_file(
        self,
        request: DownloadRequest,
        file: RemoteFile,
        *,
        local_dir: Path,
    ) -> Path:
        if self.client is not None and hasattr(self.client, "download_file"):
            return Path(self.client.download_file(request, file, local_dir=local_dir, cache_dir=self._cache_dir()))
        self.download_snapshot(request, local_dir, DownloadProgressTracker(()))
        return local_dir / file.path

    def download_snapshot(
        self,
        request: DownloadRequest,
        target_dir: Path,
        progress: DownloadProgressTracker,
        cancel_token: threading.Event | None = None,
    ) -> Path:
        if self.client is not None and hasattr(self.client, "snapshot_download"):
            return Path(
                self.client.snapshot_download(
                    request,
                    local_dir=target_dir,
                    cache_dir=self._cache_dir(),
                )
            )
        try:
            snapshot_download = self._import_snapshot_download()
        except ImportError as exc:
            raise DownloadProviderNotInstalledError("modelscope-hub 未安装，请安装下载依赖。") from exc

        try:
            result = self._call_supported_kwargs(
                snapshot_download,
                model_id=request.repo_id,
                repo_id=request.repo_id,
                revision=request.revision or "master",
                cache_dir=str(self._cache_dir()),
                local_dir=str(target_dir),
                local_files_only=request.local_files_only,
                allow_patterns=list(request.allow_patterns) if request.allow_patterns else None,
                ignore_patterns=list(request.ignore_patterns) if request.ignore_patterns else None,
                allow_file_pattern=list(request.allow_patterns) if request.allow_patterns else None,
                ignore_file_pattern=list(request.ignore_patterns) if request.ignore_patterns else None,
                endpoint=self._endpoint(),
                token=self._token(),
            )
        except Exception as exc:
            raise self._map_modelscope_error(exc) from exc
        return Path(result or target_dir)

    def _create_hub_api(self, cls):
        kwargs = {"endpoint": self._endpoint(), "token": self._token()}
        try:
            return self._call_supported_kwargs(cls, **kwargs)
        except TypeError:
            return cls()

    def _import_snapshot_download(self):
        try:
            from modelscope_hub.compat import snapshot_download

            return snapshot_download
        except ImportError:
            from modelscope_hub import snapshot_download

            return snapshot_download

    def _repo_file_list_func(self, api):
        for name in ("get_model_files", "list_repo_files"):
            func = getattr(api, name, None)
            if callable(func):
                return func
        raise AttributeError("ModelScope HubApi does not provide a repository file listing method.")

    def _call_supported_kwargs(self, func, **kwargs):
        filtered = {key: value for key, value in kwargs.items() if value is not None}
        try:
            signature = inspect.signature(func)
        except (TypeError, ValueError):
            return func(**filtered)
        if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()):
            return func(**filtered)
        return func(**{key: value for key, value in filtered.items() if key in signature.parameters})

    def _map_modelscope_error(self, exc: Exception):
        text = redact_sensitive_text(str(exc)) or ""
        lowered = text.lower()
        if "local_files_only" in lowered or ("cache" in lowered and ("not found" in lowered or "missing" in lowered)):
            return ModelScopeLocalFilesNotFoundError("魔塔本地缓存中未找到该模型文件。")
        if "401" in text or "unauthorized" in lowered or "forbidden" in lowered or "403" in text:
            return ModelScopeAuthRequiredError("魔塔社区认证失败，请检查 Token。")
        if "404" in text or "not found" in lowered or "repo not exist" in lowered:
            return ModelScopeRepoNotFoundError("魔塔社区未找到该模型。")
        if "connection" in lowered or "timeout" in lowered or "network" in lowered:
            return ModelScopeNetworkError("魔塔社区网络请求失败。")
        return ModelScopeDownloadError(text or "魔塔模型下载失败。")
