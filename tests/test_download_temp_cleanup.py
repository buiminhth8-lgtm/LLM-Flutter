import os
import time
from pathlib import Path

from llm_studio.downloads import DownloadManager, DownloadRequest, RemoteFile
from llm_studio.downloads.exceptions import DownloadNetworkError
from llm_studio.jobs import JobQueue, JobRepository, JobStatus
from llm_studio.storage.cache_manager import CacheManager, CleanupPreviewItem


class TinyConfig:
    def __init__(self, root: Path):
        self.config_path = root / "config.yaml"
        self._data = {
            "models": {
                "root_dir": str(root / "models"),
                "temp_dir": str(root / "downloads"),
                "metadata_cache": str(root / "model_index.json"),
                "adapters_dir": str(root / "adapters"),
                "minimum_free_space_gb": 0,
                "allow_external_paths": True,
                "follow_symlinks": False,
            },
            "storage": {
                "trash_dir": str(root / "trash"),
                "benchmarks_dir": str(root / "benchmarks"),
                "jobs_dir": str(root / "jobs"),
                "diagnostics_dir": str(root / "diagnostics"),
                "cleanup": {"incomplete_download_days": 0},
            },
            "uploads": {"temp_dir": str(root / "uploads")},
            "downloads": {
                "default_provider": "modelscope",
                "providers": {"modelscope": {"cache_dir": str(root / "ms-cache")}},
            },
            "external_models": [],
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class FailingDownloadClient:
    def list_files(self, request):
        return [RemoteFile("model.safetensors", 5)]

    def download_file(self, request, file, *, local_dir, cache_dir=None):
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "partial.bin").write_bytes(b"part")
        raise DownloadNetworkError("network failed")


def _make_old(path: Path) -> None:
    old = time.time() - 86400
    os.utime(path, (old, old))


def test_failed_download_records_temp_dir_and_cleanup_preview(tmp_path):
    config = TinyConfig(tmp_path)
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    manager = DownloadManager(config, queue, modelscope_client=FailingDownloadClient())

    job = manager.create_download(DownloadRequest(repo_id="org/model"))
    queue.shutdown(wait=True)
    stored = repo.get(job.id)
    temp_dir = Path(stored.payload["temp_dir"])
    _make_old(temp_dir)

    preview = CacheManager(config).preview_cleanup({"download_temp"})

    assert stored.status == JobStatus.FAILED.value
    assert stored.payload["download_temp_dir"] == str(temp_dir)
    assert temp_dir.exists()
    assert any(item.category == "download_temp" and item.job_id == job.id for item in preview)


def test_cancelled_and_failed_download_temp_dirs_are_cleanable(tmp_path):
    config = TinyConfig(tmp_path)
    failed = tmp_path / "downloads" / "job-failed1234567890-org--model"
    cancelled = tmp_path / "downloads" / "job-cancelled123456-org--model"
    final_model = tmp_path / "models" / "transformers" / "ready"
    global_modelscope_cache = tmp_path / "global-modelscope-cache"
    for path in (failed, cancelled, final_model, global_modelscope_cache):
        path.mkdir(parents=True)
        (path / "x.bin").write_bytes(b"x")
        _make_old(path)

    manager = CacheManager(config)
    preview = manager.preview_cleanup({"download_temp"})
    result = manager.cleanup_preview_items(preview)

    preview_paths = {Path(item.path) for item in preview}
    assert failed in preview_paths
    assert cancelled in preview_paths
    assert final_model not in preview_paths
    assert global_modelscope_cache not in preview_paths
    assert not failed.exists()
    assert not cancelled.exists()
    assert final_model.exists()
    assert global_modelscope_cache.exists()
    assert result["errors"] == []


def test_download_temp_cleanup_failure_has_stable_error_code(tmp_path):
    config = TinyConfig(tmp_path)
    outside = tmp_path / "outside" / "job-outside"
    outside.mkdir(parents=True)
    item = CleanupPreviewItem(
        str(outside),
        "download_temp",
        1,
        "stale_download_temp",
        job_id="job-outside",
    )

    result = CacheManager(config).cleanup_preview_items([item])

    assert result["removed"] == []
    assert result["errors"][0]["error_code"] == "DOWNLOAD_TEMP_CLEANUP_FAILED"
