"""Diagnostic package export."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

from llm_studio.config_io import redact_config
from llm_studio.models.repository import LocalModelRepository
from llm_studio.models.storage import layout_from_config
from llm_studio.runtime.capabilities import detect_runtime_capabilities
from llm_studio.storage import collect_disk_usage
from llm_studio.version import get_version_info


def redact_path(path: str) -> str:
    home = str(Path.home())
    return path.replace(home, "%USERPROFILE%")


def diagnostic_manifest() -> list[str]:
    return [
        "runtime.json",
        "version.json",
        "pip-freeze.txt",
        "config-redacted.yaml",
        "models-summary.json",
        "disk-usage.json",
    ]


def export_diagnostics(config, output_path: str | Path | None = None) -> Path:
    layout = layout_from_config(config)
    layout.ensure()
    output = Path(output_path) if output_path else layout.diagnostics_dir / "diagnostics.zip"
    caps = detect_runtime_capabilities(run_bnb_probe=False)
    runtime = caps.__dict__.copy()
    version = get_version_info()
    try:
        pip_freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True, stderr=subprocess.STDOUT, timeout=20)
    except Exception as exc:
        pip_freeze = f"pip freeze failed: {exc}\n"
    models = [
        {**model.to_dict(), "path": redact_path(str(model.path))}
        for model in LocalModelRepository(config).list_models(refresh=False)
    ]
    disk = [
        {**item.to_dict(), "path": redact_path(str(item.path))}
        for item in collect_disk_usage(config)
    ]

    import yaml

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("runtime.json", json.dumps(runtime, ensure_ascii=False, indent=2, default=str))
        archive.writestr("version.json", json.dumps(version, ensure_ascii=False, indent=2, default=str))
        archive.writestr("pip-freeze.txt", pip_freeze)
        archive.writestr(
            "config-redacted.yaml",
            yaml.safe_dump(redact_config(config._data), allow_unicode=True, sort_keys=False),
        )
        archive.writestr("models-summary.json", json.dumps(models, ensure_ascii=False, indent=2))
        archive.writestr("disk-usage.json", json.dumps(disk, ensure_ascii=False, indent=2))
    os.replace(output, output)
    return output
