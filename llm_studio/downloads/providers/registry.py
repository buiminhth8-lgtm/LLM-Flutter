"""Download provider registry."""

from __future__ import annotations

from llm_studio.downloads.exceptions import (
    DownloadProviderNotInstalledError,
    DownloadProviderNotSupportedError,
)

from .huggingface import HuggingFaceDownloadProvider
from .modelscope import ModelScopeDownloadProvider


def get_download_provider(name: str, config, *, hf_client=None, modelscope_client=None):
    normalized = (name or "huggingface").strip().lower()
    if normalized in {"huggingface", "hf"}:
        return HuggingFaceDownloadProvider(config, client=hf_client)
    if normalized in {"modelscope", "ms"}:
        if modelscope_client is None:
            try:
                import modelscope_hub  # noqa: F401
            except ImportError as exc:
                raise DownloadProviderNotInstalledError(
                    "modelscope-hub 未安装，请安装下载依赖。"
                ) from exc
        return ModelScopeDownloadProvider(config, client=modelscope_client)
    raise DownloadProviderNotSupportedError(f"不支持的下载源: {name}")
