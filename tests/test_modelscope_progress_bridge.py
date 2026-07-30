from llm_studio.downloads.modelscope_progress import ModelScopeProgressBridge
from llm_studio.downloads.progress import DownloadProgressTracker, RemoteFile


def test_modelscope_progress_callback_updates_bytes_total_speed_and_eta(monkeypatch):
    ticks = iter(float(item) for item in range(20))
    monkeypatch.setattr("llm_studio.downloads.progress.time.monotonic", lambda: next(ticks))
    tracker = DownloadProgressTracker([RemoteFile("model.safetensors", 100)])
    snapshots = []
    bridge = ModelScopeProgressBridge(tracker, snapshots.append, throttle_seconds=0)
    callback_cls = bridge.callback_class()

    callback = callback_cls("model.safetensors", 100)
    callback.update(25)
    callback.update(25)
    callback.end()

    assert snapshots[-1].downloaded_bytes == 100
    assert snapshots[-1].total_bytes == 100
    assert snapshots[-1].completed_files == 1
    assert snapshots[-1].speed_bytes_per_second is not None
    assert snapshots[-1].eta_seconds == 0
    assert snapshots[-1].current_file == "model.safetensors"


def test_modelscope_progress_unknown_total_keeps_total_and_percent_unknown():
    tracker = DownloadProgressTracker([RemoteFile("model.safetensors", None)])
    snapshots = []
    bridge = ModelScopeProgressBridge(tracker, snapshots.append, throttle_seconds=0)
    callback_cls = bridge.callback_class()

    callback = callback_cls("model.safetensors", 0)
    callback.update(25)
    callback.end()

    assert snapshots[-1].downloaded_bytes == 25
    assert snapshots[-1].total_bytes is None
    assert snapshots[-1].as_fraction() == 1.0
