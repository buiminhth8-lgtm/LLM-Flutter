"""Structured diagnostics collector used by API and CLI export."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from typing import Any

from llm_studio.capabilities import get_capabilities_for_config
from llm_studio.config_io import redact_config
from llm_studio.models.repository import LocalModelRepository
from llm_studio.runtime.capabilities import detect_runtime_capabilities
from llm_studio.storage import collect_disk_usage
from llm_studio.version import get_version_info

from .redaction import redact_mapping, redact_path, redact_text


def safe_pip_freeze() -> str:
    try:
        return subprocess.check_output(
            [sys.executable, "-m", "pip", "freeze"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
    except Exception as exc:
        return f"pip freeze failed: {redact_text(str(exc))}\n"


def collect_system_summary() -> dict[str, Any]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "executable": redact_path(sys.executable, label="python"),
    }


def collect_diagnostics(config) -> dict[str, Any]:
    caps = detect_runtime_capabilities(run_bnb_probe=False)
    runtime = redact_mapping(caps.__dict__.copy())
    try:
        models = [
            {
                **model.to_dict(),
                "path": redact_path(model.path, label="model"),
            }
            for model in LocalModelRepository(config).list_models(refresh=False)
        ]
    except Exception as exc:
        models = [{"error": redact_text(str(exc))}]
    try:
        disk = [
            {
                **item.to_dict(),
                "path": redact_path(item.path, label="data"),
            }
            for item in collect_disk_usage(config)
        ]
    except Exception as exc:
        disk = [{"error": redact_text(str(exc))}]
    return {
        "runtime": runtime,
        "version": get_version_info(),
        "system": collect_system_summary(),
        "pip_freeze": safe_pip_freeze(),
        "config_redacted": redact_mapping(redact_config(config._data)),
        "models_summary": models,
        "disk_usage": disk,
        "capabilities": [
            capability.to_dict()
            for capability in get_capabilities_for_config(config)
        ],
    }


def diagnostics_as_json(payload: Any) -> str:
    return json.dumps(redact_mapping(payload), ensure_ascii=False, indent=2, default=str)
