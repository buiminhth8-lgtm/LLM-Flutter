import zipfile

import pytest

from scripts.backup_data import create_backup
from scripts.restore_data import restore_backup


def test_backup_excludes_model_weights_and_restore_requires_confirm(tmp_path):
    data_dir = tmp_path / "data"
    (data_dir / "novels").mkdir(parents=True)
    (data_dir / "models" / "big-model").mkdir(parents=True)
    (data_dir / "novels" / "novels.sqlite").write_text("db", encoding="utf-8")
    (data_dir / "models" / "big-model" / "model.safetensors").write_text("weights", encoding="utf-8")

    backup = create_backup(data_dir, tmp_path / "backups")

    with zipfile.ZipFile(backup) as archive:
        names = archive.namelist()
    assert "data/novels/novels.sqlite" in names
    assert not any("model.safetensors" in name for name in names)

    restore_dir = tmp_path / "restore"
    with pytest.raises(ValueError, match="confirm"):
        restore_backup(backup, restore_dir)
    result = restore_backup(backup, restore_dir, confirm=True)
    assert result["status"] == "ok"
    assert (restore_dir / "novels" / "novels.sqlite").read_text(encoding="utf-8") == "db"
