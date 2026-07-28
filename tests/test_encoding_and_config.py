from pathlib import Path

import yaml

from llm_studio.config import Config


def test_python_files_are_utf8_readable():
    for path in Path("llm_studio").rglob("*.py"):
        path.read_text(encoding="utf-8")


def test_config_yaml_loads_utf8():
    with open("config.yaml", encoding="utf-8") as file:
        assert yaml.safe_load(file) is not None


def test_config_loads_legacy_minimal_config(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("models_dir: ./models\nrag:\n  chunk_size: 300\n", encoding="utf-8")
    cfg = Config(cfg_path)
    assert cfg.runtime["trust_remote_code"] is False
    assert cfg.get("rag")["chunk_size"] == 300
    assert cfg.models_dir == (tmp_path / "models").resolve()


def test_config_loads_rtx5060_example():
    cfg = Config("configs/rtx5060_laptop_8gb.yaml")
    assert cfg.runtime["device"] == "cuda"
    assert cfg.runtime["trust_remote_code"] is False
