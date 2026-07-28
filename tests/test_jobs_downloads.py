from pathlib import Path

from llm_studio.downloads import DownloadManager, DownloadRequest, DownloadTaskState
from llm_studio.jobs import Job, JobQueue, JobRepository, JobStatus, JobType, sanitize_payload
from llm_studio.jobs.exceptions import JobNotImplementedError


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
            },
            "huggingface": {"cache_dir": str(root / "hf")},
            "external_models": [],
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class FakeHFClient:
    def snapshot_download(self, request, *, local_dir, cache_dir=None):
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "config.json").write_text("{}", encoding="utf-8")
        (local_dir / "model.safetensors").write_bytes(b"x")
        return local_dir


def test_job_repository_marks_running_interrupted(tmp_path):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    job = Job.new("job-1", JobType.MODEL_SCAN.value, {})
    repo.save(job.with_update(status=JobStatus.RUNNING.value))
    repo.mark_running_interrupted()
    assert repo.get("job-1").status == JobStatus.INTERRUPTED.value


def test_payload_sanitization_removes_tokens():
    payload = sanitize_payload({"repo_id": "a/b", "token": "secret", "nested": {"api_key": "x"}})
    assert "token" not in payload
    assert "api_key" not in payload["nested"]


def test_download_manager_does_not_store_token(tmp_path):
    config = TinyConfig(tmp_path)
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    manager = DownloadManager(config, queue, hf_client=FakeHFClient())

    job = manager.create_download(DownloadRequest(repo_id="org/model", token="hf_secret"))

    stored = repo.get(job.id)
    assert "token" not in stored.payload
    queue.shutdown(wait=True)
    assert (tmp_path / "models" / "transformers" / "org--model").exists()


def test_download_task_state_does_not_fake_unknown_totals(tmp_path):
    job = Job.new(
        "job-download",
        JobType.MODEL_DOWNLOAD.value,
        {"repo_id": "org/model", "revision": None},
    )
    state = DownloadTaskState.from_job(job)

    assert state.total_bytes is None
    assert state.downloaded_bytes is None
    assert state.resume_supported is True
    assert state.can_cancel is True


def test_queue_success_transition(tmp_path):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    job = queue.submit(JobType.MODEL_SCAN.value, {}, lambda job, update, cancel: update(1.0, "ok"))
    queue.shutdown(wait=True)
    assert repo.get(job.id).status == JobStatus.SUCCEEDED.value


def test_queue_not_implemented_becomes_failed(tmp_path):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    job = queue.submit(
        JobType.LORA_MERGE.value,
        {},
        lambda job, update, cancel: (_ for _ in ()).throw(JobNotImplementedError("nope")),
    )
    queue.shutdown(wait=True)
    stored = repo.get(job.id)
    assert stored.status == JobStatus.FAILED.value
    assert stored.error_code == "JobNotImplementedError"
