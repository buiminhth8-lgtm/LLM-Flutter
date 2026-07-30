"""Download provider registry."""

from __future__ import annotations

from llm_studio.downloads.exceptions import (
    DownloadProviderNotInstalledError,
    DownloadProviderNotSupportedError,
)

from .modelscope import ModelScopeDownloadProvider


def get_download_provider(name: str | None, config, *, modelscope_client=None):
    normalized = (name or "modelscope").strip().lower()
    if normalized in {"modelscope", "ms"}:
        if modelscope_client is None:
            try:
                import modelscope_hub  # noqa: F401
            except ImportError as exc:
                raise DownloadProviderNotInstalledError(
                    "modelscope-hub is not installed. Install the download dependency first."
                ) from exc
        return ModelScopeDownloadProvider(config, client=modelscope_client)
    raise DownloadProviderNotSupportedError(
        f"Download provider '{name}' is not supported. ModelScope is the only remote download provider."
    )
