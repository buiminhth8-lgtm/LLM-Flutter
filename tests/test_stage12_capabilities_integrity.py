from llm_studio.capabilities import CapabilityStatus, get_capabilities_for_config
from llm_studio.config import Config


def test_stage12_capabilities_are_available_when_novel_studio_enabled(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
features:
  novel_studio:
    enabled: true
  evaluation_center:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )
    caps = {cap.name: cap for cap in get_capabilities_for_config(Config(cfg_path))}

    assert caps["novel_studio_product_ui"].status == CapabilityStatus.AVAILABLE
    assert caps["health_checks"].status == CapabilityStatus.AVAILABLE
    assert caps["diagnostics_export"].status == CapabilityStatus.AVAILABLE
    assert caps["backup_restore"].status == CapabilityStatus.AVAILABLE
    assert caps["windows_desktop_release"].status == CapabilityStatus.AVAILABLE
    assert caps["windows_packaging"].status == CapabilityStatus.AVAILABLE


def test_stage12_does_not_change_core_business_capabilities(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
features:
  novel_studio:
    enabled: true
  evaluation_center:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
""",
        encoding="utf-8",
    )
    caps = {cap.name: cap for cap in get_capabilities_for_config(Config(cfg_path))}

    assert caps["writing_workspace"].status == CapabilityStatus.AVAILABLE
    assert caps["revision_system"].status == CapabilityStatus.AVAILABLE
    assert caps["dataset_builder"].status == CapabilityStatus.AVAILABLE
    assert caps["finetune_center"].status == CapabilityStatus.AVAILABLE
    assert caps["full_evaluation_center"].status == CapabilityStatus.AVAILABLE
