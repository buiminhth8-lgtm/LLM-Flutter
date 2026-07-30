import pytest

from llm_studio.downloads.exceptions import (
    DownloadProviderNotInstalledError,
    DownloadProviderNotSupportedError,
)
from llm_studio.downloads.providers.modelscope import ModelScopeDownloadProvider
from llm_studio.downloads.providers.registry import get_download_provider


class TinyConfig:
    def get(self, key, default=None):
        return {
            "models": {
                "root_dir": "./data/models",
                "temp_dir": "./data/downloads",
                "metadata_cache": "./data/model_index.json",
                "minimum_free_space_gb": 0,
            }
        }.get(key, default)


def test_registry_returns_modelscope_provider_with_fake_client():
    provider = get_download_provider("modelscope", TinyConfig(), modelscope_client=object())

    assert isinstance(provider, ModelScopeDownloadProvider)


def test_registry_defaults_to_modelscope_provider_with_fake_client():
    provider = get_download_provider(None, TinyConfig(), modelscope_client=object())

    assert isinstance(provider, ModelScopeDownloadProvider)


def test_registry_rejects_huggingface_provider():
    with pytest.raises(DownloadProviderNotSupportedError) as error:
        get_download_provider("huggingface", TinyConfig())

    assert error.value.error_code == "DOWNLOAD_PROVIDER_NOT_SUPPORTED"


def test_registry_rejects_unknown_provider():
    with pytest.raises(DownloadProviderNotSupportedError) as error:
        get_download_provider("unknown", TinyConfig())

    assert error.value.error_code == "DOWNLOAD_PROVIDER_NOT_SUPPORTED"


def test_registry_reports_modelscope_dependency_missing(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "modelscope_hub":
            raise ImportError(name)
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(DownloadProviderNotInstalledError) as error:
        get_download_provider("modelscope", TinyConfig())

    assert error.value.error_code == "DOWNLOAD_PROVIDER_NOT_INSTALLED"
