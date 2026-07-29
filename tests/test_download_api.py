import pytest

from llm_studio.config import Config
from llm_studio.downloads.exceptions import (
    DownloadCancelNotAllowedError,
    DownloadRetryNotAllowedError,
)
from llm_studio.jobs import Job, JobStatus, JobType
from llm_studio.jobs.exceptions import JobNotFoundError


def _write_config(path):
    path.write_text(
        """
auth:
  enabled: false
api:
  allowed_origins: []
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
storage:
  jobs_dir: ./data/jobs
""",
        encoding="utf-8",
    )


class FakeDownloadManager:
    last_request = None

    def __init__(self, config, job_queue, hf_client=None, model_repository=None):
        self.job_queue = job_queue

    def create_download(self, request):
        FakeDownloadManager.last_request = request
        return Job.new(
            "job-created",
            JobType.MODEL_DOWNLOAD.value,
            {"repo_id": request.repo_id, "revision": request.revision},
        )

    def cancel_job(self, job_id):
        if job_id == "missing":
            raise JobNotFoundError(job_id)
        if job_id == "terminal":
            raise DownloadCancelNotAllowedError("not allowed")
        return Job.new(job_id, JobType.MODEL_DOWNLOAD.value, {"repo_id": "org/model"}).with_update(
            status=JobStatus.CANCELLING.value,
        )

    def retry_interrupted(self, job):
        raise DownloadRetryNotAllowedError("not allowed")


def test_download_api_create_forwards_patterns(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio import api_server

    monkeypatch.setattr(api_server, "DownloadManager", FakeDownloadManager)
    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)

    client = TestClient(api_server.get_app(Config(cfg_path)))
    response = client.post(
        "/v1/downloads",
        json={
            "repo_id": "org/model",
            "revision": "main",
            "allow_patterns": ["*.json"],
            "ignore_patterns": ["*.md"],
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-created"
    assert FakeDownloadManager.last_request.repo_id == "org/model"
    assert FakeDownloadManager.last_request.allow_patterns == ("*.json",)
    assert FakeDownloadManager.last_request.ignore_patterns == ("*.md",)
    assert FakeDownloadManager.last_request.token is None


def test_download_api_not_found_and_retry_not_allowed(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio import api_server

    monkeypatch.setattr(api_server, "DownloadManager", FakeDownloadManager)
    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)

    client = TestClient(api_server.get_app(Config(cfg_path)))
    missing = client.get("/v1/downloads/missing")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "DOWNLOAD_NOT_FOUND"

    assert api_server._job_repository is not None
    api_server._job_repository.save(
        Job.new("job-succeeded", JobType.MODEL_DOWNLOAD.value, {"repo_id": "org/model"}).with_update(
            status=JobStatus.SUCCEEDED.value,
        )
    )
    retry = client.post("/v1/downloads/job-succeeded/retry")
    assert retry.status_code == 409
    assert retry.json()["error"]["code"] == "DOWNLOAD_RETRY_NOT_ALLOWED"

    cancel = client.post("/v1/downloads/missing/cancel")
    assert cancel.status_code == 404
    assert cancel.json()["error"]["code"] == "DOWNLOAD_NOT_FOUND"

    terminal_cancel = client.post("/v1/downloads/terminal/cancel")
    assert terminal_cancel.status_code == 409
    assert terminal_cancel.json()["error"]["code"] == "DOWNLOAD_CANCEL_NOT_ALLOWED"


def test_jobs_api_redacts_public_payload(monkeypatch, tmp_path):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from llm_studio import api_server

    monkeypatch.setattr(api_server, "DownloadManager", FakeDownloadManager)
    cfg_path = tmp_path / "config.yaml"
    _write_config(cfg_path)

    client = TestClient(api_server.get_app(Config(cfg_path)))
    assert api_server._job_repository is not None
    job = Job.new(
        "job-sensitive",
        JobType.RAG_REBUILD.value,
        {
            "repo_id": "org/model",
            "file_path": str(tmp_path / "secret.txt"),
            "directory_path": str(tmp_path / "secret-dir"),
            "token": "hf_secret",
        },
    )
    api_server._job_repository.save(job)

    listed = client.get("/v1/jobs").json()["data"][0]
    detail = client.get("/v1/jobs/job-sensitive").json()

    assert listed["payload"]["repo_id"] == "org/model"
    assert listed["payload"]["file_path"] == "<redacted>"
    assert listed["payload"]["directory_path"] == "<redacted>"
    assert listed["payload"]["token"] == "<redacted>"
    assert detail["payload"]["file_path"] == "<redacted>"
    assert api_server._job_repository.get("job-sensitive").payload["file_path"] == str(tmp_path / "secret.txt")
