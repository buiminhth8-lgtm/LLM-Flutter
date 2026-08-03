"""Diagnostic package export."""

from __future__ import annotations

import os
import zipfile
from pathlib import Path

from llm_studio.models.storage import layout_from_config

from .collector import collect_diagnostics, diagnostics_as_json
from .redaction import redact_path as redact_path


def diagnostic_manifest() -> list[str]:
    return [
        "runtime.json",
        "version.json",
        "system.json",
        "pip-freeze.txt",
        "config-redacted.json",
        "models-summary.json",
        "disk-usage.json",
        "capabilities.json",
    ]


def export_diagnostics(config, output_path: str | Path | None = None) -> Path:
    layout = layout_from_config(config)
    layout.ensure()
    output = Path(output_path) if output_path else layout.diagnostics_dir / "diagnostics.zip"
    payload = collect_diagnostics(config)

    output.parent.mkdir(parents=True, exist_ok=True)
    tmp_output = output.with_suffix(output.suffix + ".tmp")
    try:
        with zipfile.ZipFile(tmp_output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("runtime.json", diagnostics_as_json(payload["runtime"]))
            archive.writestr("version.json", diagnostics_as_json(payload["version"]))
            archive.writestr("system.json", diagnostics_as_json(payload["system"]))
            archive.writestr("pip-freeze.txt", payload["pip_freeze"])
            archive.writestr("config-redacted.json", diagnostics_as_json(payload["config_redacted"]))
            archive.writestr("models-summary.json", diagnostics_as_json(payload["models_summary"]))
            archive.writestr("disk-usage.json", diagnostics_as_json(payload["disk_usage"]))
            archive.writestr("capabilities.json", diagnostics_as_json(payload["capabilities"]))
        os.replace(tmp_output, output)
    except Exception:
        if tmp_output.exists():
            tmp_output.unlink()
        raise
    return output


def main() -> None:
    import argparse

    from llm_studio.config import Config

    parser = argparse.ArgumentParser(description="Export a redacted LLM Studio diagnostics package.")
    parser.add_argument("--config", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    config = Config(args.config) if args.config else Config()
    print(export_diagnostics(config, args.output))


if __name__ == "__main__":
    main()
