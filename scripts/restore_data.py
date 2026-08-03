"""Restore a local LLM Studio data backup."""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path


def _validate_member(member: str) -> Path:
    relative = Path(member)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe zip member: {member}")
    return relative


def restore_backup(backup_zip: str | Path, data_dir: str | Path, *, confirm: bool = False) -> dict[str, object]:
    if not confirm:
        raise ValueError("Restore requires --confirm.")
    backup_path = Path(backup_zip).resolve()
    target_root = Path(data_dir).resolve()
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup does not exist: {backup_path}")
    target_root.mkdir(parents=True, exist_ok=True)
    restored: list[str] = []
    with zipfile.ZipFile(backup_path) as archive:
        manifest = json.loads(archive.read("backup-manifest.json").decode("utf-8"))
        for member in archive.namelist():
            relative = _validate_member(member)
            if member == "backup-manifest.json" or not relative.parts or relative.parts[0] != "data":
                continue
            target_relative = Path(*relative.parts[1:])
            target = target_root / target_relative
            if member.endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member) as source, target.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            restored.append(target_relative.as_posix())
    return {"status": "ok", "restored_files": restored, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore a local LLM Studio data backup.")
    parser.add_argument("--backup", required=True)
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    print(json.dumps(restore_backup(args.backup, args.data_dir, confirm=args.confirm), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
