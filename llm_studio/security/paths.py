"""Safe local path resolution for admin-only import endpoints."""

from __future__ import annotations

from pathlib import Path


class PathSecurityError(ValueError):
    """Raised when a user-provided local path is not allowed."""


def _is_unc_path(raw_path: str) -> bool:
    return raw_path.startswith("\\\\") or raw_path.startswith("//")


def resolve_allowed_path(
    raw_path: str,
    allowed_roots: list[Path],
    *,
    must_exist: bool = True,
    allow_file: bool = True,
    allow_dir: bool = True,
) -> Path:
    """Resolve a local path and require it to stay inside configured roots."""
    text = (raw_path or "").strip()
    if not text:
        raise PathSecurityError("本地路径不能为空。")
    if _is_unc_path(text):
        raise PathSecurityError("不允许使用 UNC 网络路径。")
    if not allowed_roots:
        raise PathSecurityError("未配置允许访问的本地路径根目录。")

    resolved = Path(text).expanduser().resolve()
    if must_exist and not resolved.exists():
        raise PathSecurityError("本地路径不存在。")
    if resolved.is_file() and not allow_file:
        raise PathSecurityError("当前接口不允许使用文件路径。")
    if resolved.is_dir() and not allow_dir:
        raise PathSecurityError("当前接口不允许使用目录路径。")
    if not resolved.is_file() and not resolved.is_dir() and must_exist:
        raise PathSecurityError("本地路径类型不受支持。")

    roots = [root.expanduser().resolve() for root in allowed_roots]
    if not any(resolved.is_relative_to(root) for root in roots):
        raise PathSecurityError("本地路径不在允许访问的目录内。")
    return resolved
