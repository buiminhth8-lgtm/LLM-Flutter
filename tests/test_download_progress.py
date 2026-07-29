import threading
import time
from pathlib import Path

import pytest

from llm_studio.downloads import (
    DownloadManager,
    DownloadProgressTracker,
    DownloadRequest,
    DownloadTaskState,
    RemoteFile,
)
from llm_studio.downloads.exceptions import DownloadRetryNotAllowedError
from llm_studio.jobs import Job, JobQueue, JobRepository, JobStatus, JobType


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
                "jobs_dir": str(root / "jobs"),
            },
            "huggingface": {"cache_dir": str(root / "hf")},
            "external_models": [],
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class FakeHFClient:
    files = (
        RemoteFile("config.json", 23),
        RemoteFile("model.safetensors", 5),
    )

    def list_files(self, request):
        return list(self.files)

    def download_file(self, request, file, *, local_dir, cache_dir=None):
        target = local_dir / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if file.path == "config.json":
            target.write_text('{"model_type":"llama"}', encoding="utf-8")
        else:
            target.write_bytes(b"12345")
        return target


class UnknownTotalHFClient(FakeHFClient):
    files = (
        RemoteFile("config.json", None),
        RemoteFile("model.safetensors", None),
    )


class BlockingHFClient(FakeHFClient):
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()

    def download_file(self, request, file, *, local_dir, cache_dir=None):
        self.started.set()
        self.release.wait(timeout=2)
        return super().download_file(request, file, local_dir=local_dir, cache_dir=cache_dir)


def _manager(tmp_path, hf_client):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    return DownloadManager(TinyConfig(tmp_path), queue, hf_client=hf_client), repo, queue


def _wait_for_terminal(repo: JobRepository, job_id: str) -> Job:
    terminal = {JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value}
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = repo.get(job_id)
        if job.status in terminal:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not finish")


def test_download_progress_tracker_calculates_percent_speed_and_eta(monkeypatch):
    ticks = iter([0.0, 2.0])
    monkeypatch.setattr("llm_studio.downloads.progress.time.monotonic", lambda: next(ticks))
    tracker = DownloadProgressTracker([RemoteFile("a.bin", 100)])

    progress = tracker.complete_file("a.bin", size_bytes=50)

    assert progress.total_bytes == 100
    assert progress.as_fraction() == 0.5
    assert progress.speed_bytes_per_second == 25
    assert progress.eta_seconds == 2


def test_unknown_total_bytes_keep_percent_null():
    tracker = DownloadProgressTracker([RemoteFile("a.bin", None)])
    progress = tracker.complete_file("a.bin", size_bytes=10)

    state = DownloadTaskState.from_job(
        Job.new(
            "job-a",
            JobType.MODEL_DOWNLOAD.value,
            {
                "repo_id": "org/model",
                "downloaded_bytes": progress.downloaded_bytes,
                "total_bytes": progress.total_bytes,
            },
        )
    )

    assert state.total_bytes is None
    assert state.percent is None


def test_download_success_scans_and_registers_model(tmp_path):
    manager, repo, queue = _manager(tmp_path, FakeHFClient())

    job = manager.create_download(DownloadRequest(repo_id="org/model", token="hf_secret"))
    queue.shutdown(wait=True)

    stored = repo.get(job.id)
    state = DownloadTaskState.from_job(stored)
    assert stored.status == JobStatus.SUCCEEDED.value
    assert "token" not in stored.payload
    assert state.downloaded_bytes == 28
    assert state.total_bytes == 28
    assert state.percent == 100.0
    assert state.registration_status == "succeeded"
    assert state.model_id
    assert (tmp_path / "models" / "transformers" / "org--model").exists()


def test_download_cancel_sets_cancelled_state(tmp_path):
    hf_client = BlockingHFClient()
    manager, repo, queue = _manager(tmp_path, hf_client)

    job = manager.create_download(DownloadRequest(repo_id="org/model"))
    assert hf_client.started.wait(timeout=2)
    manager.cancel_job(job.id)
    hf_client.release.set()
    queue.shutdown(wait=True)

    stored = repo.get(job.id)
    state = DownloadTaskState.from_job(stored)
    assert stored.status == JobStatus.CANCELLED.value
    assert stored.error_code == "DOWNLOAD_CANCELLED"
    assert state.cancel_requested is True
    assert state.can_retry is True


def test_retry_allowed_for_cancelled_and_rejected_for_succeeded(tmp_path):
    manager, repo, queue = _manager(tmp_path, FakeHFClient())
    succeeded = _wait_for_terminal(repo, manager.create_download(DownloadRequest(repo_id="org/model")).id)

    with pytest.raises(DownloadRetryNotAllowedError):
        manager.retry_interrupted(succeeded)

    cancelled = succeeded.with_update(
        status=JobStatus.CANCELLED.value,
        payload={**succeeded.payload, "repo_id": "org/another", "local_name": "org--another"},
    )
    repo.save(cancelled)
    retry = manager.retry_interrupted(cancelled)
    assert retry.payload["parent_job_id"] == cancelled.id
    queue.shutdown(wait=True)


def test_unknown_file_sizes_do_not_fake_total(tmp_path):
    manager, repo, queue = _manager(tmp_path, UnknownTotalHFClient())

    job = manager.create_download(DownloadRequest(repo_id="org/model"))
    queue.shutdown(wait=True)

    state = DownloadTaskState.from_job(repo.get(job.id))
    assert state.downloaded_bytes == 27
    assert state.total_bytes is None
    assert state.percent is None
