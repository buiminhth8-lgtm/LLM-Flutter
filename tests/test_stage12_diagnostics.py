import zipfile

from llm_studio.config import Config
from llm_studio.diagnostics import collect_diagnostics, diagnostic_manifest, export_diagnostics
from tests.test_stage12_version_api import _stage12_client


def test_diagnostics_collector_redacts_paths_and_secrets(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
auth:
  enabled: false
  api_key: sk-secret-value
api:
  allowed_origins: []
features:
  novel_studio:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )
    config = Config(cfg_path)

    payload = collect_diagnostics(config)
    exported = export_diagnostics(config, tmp_path / "diagnostics.zip")

    assert "<redacted>" in str(payload)
    assert "sk-secret-value" not in str(payload)
    assert cfg_path.drive not in str(payload)
    with zipfile.ZipFile(exported) as archive:
        names = set(archive.namelist())
        assert set(diagnostic_manifest()).issubset(names)
        assert not any(name.endswith((".bin", ".safetensors", ".gguf")) for name in names)
        content = "\n".join(
            archive.read(name).decode("utf-8", errors="ignore")
            for name in names
        )
    assert "sk-secret-value" not in content
    assert cfg_path.drive not in content


def test_diagnostics_api_exposes_preview_health_system_and_capabilities(monkeypatch, tmp_path):
    client = _stage12_client(tmp_path, monkeypatch)

    assert client.get("/v1/diagnostics/health").status_code == 200
    assert client.get("/v1/diagnostics/system").status_code == 200
    capabilities = client.get("/v1/diagnostics/capabilities")
    preview = client.get("/v1/diagnostics/preview")

    assert capabilities.status_code == 200
    assert preview.status_code == 200
    assert "capabilities" in capabilities.json()
    assert "manifest" in preview.json()
