import importlib
import zipfile

import pytest

from llm_studio.diagnostics import export_diagnostics


class Config:
    def __init__(self, root):
        self.config_path = root / "config.yaml"
        self._data = {
            "api": {"api_key": "sk-secret"},
            "auth": {"password": "plain-password"},
            "downloads": {
                "providers": {
                    "modelscope": {
                        "token": "ms-secret",
                        "cache_dir": str(root / "ms-cache"),
                    }
                }
            },
            "models": {
                "root_dir": str(root / "models"),
                "temp_dir": str(root / "downloads"),
                "metadata_cache": str(root / "model_index.json"),
            },
            "storage": {
                "trash_dir": str(root / "trash"),
                "benchmarks_dir": str(root / "benchmarks"),
                "jobs_dir": str(root / "jobs"),
                "diagnostics_dir": str(root / "diagnostics"),
            },
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


def test_diagnostics_export_redacts_secrets(tmp_path):
    output = export_diagnostics(Config(tmp_path), tmp_path / "diag.zip")
    assert not (tmp_path / "diag.zip.tmp").exists()

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        text = "\n".join(archive.read(name).decode("utf-8", errors="replace") for name in names)

    assert "capabilities.json" in names
    assert "sk-secret" not in text
    assert "hf-secret" not in text
    assert "plain-password" not in text
    assert "model.safetensors" not in names


def test_diagnostics_export_failure_cleans_tmp_and_keeps_existing_output(monkeypatch, tmp_path):
    export_module = importlib.import_module("llm_studio.diagnostics.export")
    output = tmp_path / "diag.zip"
    output.write_bytes(b"old")

    class FailingZipFile:
        def __init__(self, path, *args, **kwargs):
            self.path = path

        def __enter__(self):
            self.path.write_bytes(b"partial")
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def writestr(self, *args, **kwargs):
            raise RuntimeError("zip write failed")

    monkeypatch.setattr(export_module.zipfile, "ZipFile", FailingZipFile)

    with pytest.raises(RuntimeError, match="zip write failed"):
        export_module.export_diagnostics(Config(tmp_path), output)

    assert output.read_bytes() == b"old"
    assert not (tmp_path / "diag.zip.tmp").exists()
