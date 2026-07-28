import os

import pytest

from llm_studio.security.paths import PathSecurityError, resolve_allowed_path


def test_resolve_allowed_path_accepts_file_inside_allowed_root(tmp_path):
    root = tmp_path / "imports"
    root.mkdir()
    file_path = root / "note.txt"
    file_path.write_text("hello", encoding="utf-8")

    resolved = resolve_allowed_path(str(file_path), [root], allow_file=True, allow_dir=False)

    assert resolved == file_path.resolve()


def test_resolve_allowed_path_rejects_outside_root(tmp_path):
    root = tmp_path / "imports"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    with pytest.raises(PathSecurityError):
        resolve_allowed_path(str(outside), [root])


def test_resolve_allowed_path_rejects_wrong_type(tmp_path):
    root = tmp_path / "imports"
    root.mkdir()

    with pytest.raises(PathSecurityError):
        resolve_allowed_path(str(root), [root], allow_file=True, allow_dir=False)


def test_resolve_allowed_path_rejects_symlink_escape(tmp_path):
    root = tmp_path / "imports"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    link = root / "escape.txt"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink not available in this environment: {exc}")

    with pytest.raises(PathSecurityError):
        resolve_allowed_path(str(link), [root])
