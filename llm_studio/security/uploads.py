"""Safe upload handling for API endpoints."""

from __future__ import annotations

import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import UploadFile

WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}


class UploadError(RuntimeError):
    code = "UPLOAD_SAVE_FAILED"
    status_code = 500


class UploadFilenameInvalid(UploadError):
    code = "UPLOAD_FILENAME_INVALID"
    status_code = 400


class UploadExtensionNotAllowed(UploadError):
    code = "UPLOAD_EXTENSION_NOT_ALLOWED"
    status_code = 400


class UploadFileTooLarge(UploadError):
    code = "UPLOAD_FILE_TOO_LARGE"
    status_code = 413


class UploadSaveFailed(UploadError):
    code = "UPLOAD_SAVE_FAILED"
    status_code = 500


@dataclass(frozen=True)
class UploadPolicy:
    max_size_bytes: int
    allowed_extensions: tuple[str, ...]
    allowed_mime_types: tuple[str, ...] | None
    destination_dir: Path


@dataclass(frozen=True)
class SavedUpload:
    path: Path
    original_filename: str
    safe_filename: str
    size_bytes: int


def sanitize_filename(original_filename: str) -> str:
    filename = (original_filename or "").strip()
    if not filename:
        raise UploadFilenameInvalid("上传文件名不能为空。")
    if "/" in filename or "\\" in filename or ".." in filename:
        raise UploadFilenameInvalid("上传文件名不能包含路径。")
    if re.match(r"^[a-zA-Z]:", filename):
        raise UploadFilenameInvalid("上传文件名不能是 Windows 绝对路径。")
    basename = os.path.basename(filename)
    if not basename or basename in {".", ".."}:
        raise UploadFilenameInvalid("上传文件名无效。")
    stem = Path(basename).stem.upper()
    if stem in WINDOWS_RESERVED_NAMES:
        raise UploadFilenameInvalid("上传文件名使用了 Windows 保留名称。")
    return basename


def validate_extension(filename: str, allowed_extensions: tuple[str, ...]) -> None:
    allowed = tuple(ext.lower() for ext in allowed_extensions)
    suffix = Path(filename).suffix.lower()
    if suffix not in allowed:
        raise UploadExtensionNotAllowed("不支持的上传文件扩展名。")


async def save_upload_file_safely(file: "UploadFile", policy: UploadPolicy) -> SavedUpload:
    original = sanitize_filename(file.filename or "")
    validate_extension(original, policy.allowed_extensions)
    policy.destination_dir.mkdir(parents=True, exist_ok=True)

    suffix = Path(original).suffix.lower()
    safe_filename = f"{uuid.uuid4().hex}{suffix}"
    final_path = policy.destination_dir / safe_filename
    temp_path = policy.destination_dir / f"{safe_filename}.part"
    if final_path.exists() or temp_path.exists():
        raise UploadSaveFailed("上传目标文件已存在。")

    total = 0
    try:
        with open(temp_path, "xb") as handle:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > policy.max_size_bytes:
                    raise UploadFileTooLarge("上传文件超过大小限制。")
                handle.write(chunk)
        temp_path.replace(final_path)
    except UploadError:
        temp_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        temp_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise UploadSaveFailed(f"上传文件保存失败: {exc}") from exc
    finally:
        await file.close()

    return SavedUpload(
        path=final_path,
        original_filename=original,
        safe_filename=safe_filename,
        size_bytes=total,
    )
