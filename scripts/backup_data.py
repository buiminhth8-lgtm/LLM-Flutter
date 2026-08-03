"""Create a local LLM Studio data backup without model weights."""

from __future__ import annotations

import argparse
import json
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path

EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".git",
    "models",
    "downloads",
    "backups",
    "checkpoints",
    "diagnostics",
    "trash",
}
EXCLUDED_SUFFIXES = {
    ".bin",
    ".safetensors",
    ".gguf",
    ".pt",
    ".pth",
    ".onnx",
    ".ckpt",
}


def _safe_relative(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    root_resolved = root.resolve()
    relative = resolved.relative_to(root_resolved)
    if any(part in {"..", ""} for part in relative.parts):
        raise ValueError(f"Unsafe backup path: {path}")
    return relative


def _include_file(path: Path, data_root: Path) -> bool:
    relative = _safe_relative(path, data_root)
    lowered_parts = {part.lower() for part in relative.parts}
    if lowered_parts.intersection(EXCLUDED_DIR_NAMES):
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return path.is_file()


def create_backup(data_dir: str | Path, output_dir: str | Path | None = None) -> Path:
    data_root = Path(data_dir).resolve()
    if not data_root.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_root}")
    output_root = Path(output_dir).resolve() if output_dir else data_root / "backups"
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = output_root / f"llm-studio-data-backup-{stamp}.zip"
    manifest: dict[str, object] = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": "llm-studio-stage12-backup",
        "excluded": sorted(EXCLUDED_DIR_NAMES | EXCLUDED_SUFFIXES),
        "files": [],
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(data_root.rglob("*")):
            if not _include_file(path, data_root):
                continue
            relative = _safe_relative(path, data_root).as_posix()
            archive.write(path, f"data/{relative}")
            manifest["files"].append(relative)  # type: ignore[index]
        archive.writestr("backup-manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a local LLM Studio data backup without model weights.")
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    print(create_backup(args.data_dir, args.output_dir))


if __name__ == "__main__":
    main()
