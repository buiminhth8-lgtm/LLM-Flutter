import zipfile

from llm_studio.diagnostics import export_diagnostics


class Config:
    def __init__(self, root):
        self.config_path = root / "config.yaml"
        self._data = {
            "api": {"api_key": "sk-secret"},
            "auth": {"password": "plain-password"},
            "huggingface": {"token": "hf-secret", "cache_dir": str(root / "hf")},
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

    with zipfile.ZipFile(output) as archive:
        names = set(archive.namelist())
        text = "\n".join(archive.read(name).decode("utf-8", errors="replace") for name in names)

    assert "capabilities.json" in names
    assert "sk-secret" not in text
    assert "hf-secret" not in text
    assert "plain-password" not in text
    assert "model.safetensors" not in names
