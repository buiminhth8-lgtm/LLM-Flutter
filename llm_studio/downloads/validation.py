"""Downloaded model validation."""

from __future__ import annotations

from pathlib import Path

from llm_studio.models.metadata import has_any_weight

from .exceptions import DownloadValidationError


def validate_downloaded_model(path: Path) -> None:
    if not path.exists():
        raise DownloadValidationError(f"下载目录不存在: {path}")
    if path.is_file():
        if path.suffix.lower() != ".gguf":
            raise DownloadValidationError("单文件下载当前只接受 GGUF 文件。")
        return
    if not (path / "config.json").exists() and not any(path.glob("*.gguf")):
        raise DownloadValidationError("缺少 config.json 或 GGUF 文件，无法识别模型格式。")
    if not has_any_weight(path):
        raise DownloadValidationError("缺少权重文件，下载结果不能进入正式模型目录。")

