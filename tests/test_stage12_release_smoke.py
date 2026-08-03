from pathlib import Path


def test_stage12_release_assets_exist():
    required = [
        "scripts/windows/check_environment.ps1",
        "scripts/windows/start_backend.ps1",
        "scripts/windows/start_flutter_desktop.ps1",
        "scripts/windows/export_diagnostics.ps1",
        "scripts/windows/backup_data.ps1",
        "scripts/windows/restore_data.ps1",
        "scripts/package_windows.ps1",
        "docs/NOVEL_STAGE12_PRODUCTIZATION.md",
        "docs/WINDOWS_RELEASE_GUIDE.md",
        "docs/RELEASE_CHECKLIST.md",
        "docs/DIAGNOSTICS_GUIDE.md",
        "docs/BACKUP_RESTORE_GUIDE.md",
        "docs/UPGRADE_GUIDE.md",
        "docs/RELEASE_NOTES.md",
    ]

    for path in required:
        assert Path(path).exists(), path


def test_stage12_windows_scripts_do_not_hardcode_user_paths():
    scripts = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path("scripts/windows").glob("*.ps1")
    )
    assert "C:\\Users" not in scripts
    assert "D:\\" not in scripts
    assert "sk-" not in scripts
