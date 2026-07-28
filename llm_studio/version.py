"""Application version information."""

from __future__ import annotations

import subprocess
import sys

__version__ = "1.0.0"


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
        "version": __version__,
        "git_commit": git_commit(),
        "python": sys.version,
        "torch": torch_version,
        "cuda": cuda,
        "gpu": gpu,
    }
