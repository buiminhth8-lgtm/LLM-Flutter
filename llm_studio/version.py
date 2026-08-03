"""Application version information exposed to the desktop client and diagnostics."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

from llm_studio.capabilities import get_capabilities_for_config

__version__ = "1.0.0"
APP_NAME = "LLM Studio"
NOVEL_STUDIO_STAGE = 12
RELEASE_CHANNEL = os.environ.get("LLM_STUDIO_RELEASE_CHANNEL", "local")
BUILD_ID = os.environ.get("LLM_STUDIO_BUILD", "dev")


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "unknown"


def get_version_info() -> dict[str, object]:
    try:
        import torch
        torch_version = torch.__version__
        cuda = torch.version.cuda
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        torch_version = None
        cuda = None
        gpu = None
    return {
        "app_name": APP_NAME,
        "version": __version__,
        "novel_studio_stage": NOVEL_STUDIO_STAGE,
        "release_channel": RELEASE_CHANNEL,
        "build": BUILD_ID,
        "git_commit": git_commit(),
        "python": sys.version,
        "platform": platform.platform(),
        "torch": torch_version,
        "cuda": cuda,
        "gpu": gpu,
    }


def get_version_payload(config: Any | None = None) -> dict[str, object]:
    """Return a stable, JSON-serializable payload for `/v1/version`.

    The payload intentionally contains environment/runtime versions and feature
    flags, but not API keys, local model paths, or user content.
    """

    features = {}
    if config is not None:
        raw_features = config.get("features", {})
        if isinstance(raw_features, dict):
            features = {
                name: bool(value.get("enabled", False))
                for name, value in raw_features.items()
                if isinstance(value, dict) and "enabled" in value
            }
    capabilities = [
        {
            "name": capability.name,
            "status": capability.status.value,
            "frontend_exposed": capability.frontend_exposed,
        }
        for capability in get_capabilities_for_config(config)
    ]
    return {
        **get_version_info(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "features": features,
        "capabilities": capabilities,
    }
