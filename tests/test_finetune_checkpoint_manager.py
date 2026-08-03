from __future__ import annotations

from pathlib import Path

from llm_studio.finetune.checkpoint_manager import FineTuneCheckpointManager


def test_checkpoint_manager_records_relative_safe_paths(tmp_path):
    manager = FineTuneCheckpointManager(tmp_path / "data" / "finetune")
    source = tmp_path / "source"
    source.mkdir()
    (source / "weights.bin").write_bytes(b"checkpoint")

    checkpoint = manager.record_checkpoint(
        "run-1",
        checkpoint_type="last",
        step=10,
        source_path=source,
        metrics={"train_loss": 1.2},
    )

    assert checkpoint["checkpoint_type"] == "last"
    assert checkpoint["checkpoint_hash"]
    assert checkpoint["size_bytes"] > 0
    assert ":\\" not in checkpoint["checkpoint_path"]
    assert (tmp_path / "data" / checkpoint["checkpoint_path"]).exists()


def test_checkpoint_manager_separates_best_and_last(tmp_path):
    manager = FineTuneCheckpointManager(tmp_path / "data" / "finetune")
    last = manager.record_checkpoint("run-1", checkpoint_type="last", step=1)
    best = manager.record_checkpoint("run-1", checkpoint_type="best", step=1)

    assert Path(last["checkpoint_path"]).parts[-2] == "last"
    assert Path(best["checkpoint_path"]).parts[-2] == "best"
