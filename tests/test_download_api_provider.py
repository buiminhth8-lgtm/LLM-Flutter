import pytest

from llm_studio.config import Config
from llm_studio.jobs import Job, JobType


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
downloads:
  default_provider: modelscope
""",
        encoding="utf-8",
    )


class FakeDownloadManager:
    last_request = None

    def __init__(self, config, job_queue, modelscope_client=None, model_repository=None):
        self.job_queue = job_queue

    def create_download(self, request):
        FakeDownloadManager.last_request = request
        return Job.new(
            "job-created",
            JobType.MODEL_DOWNLOAD.value,
            {"provider": request.provider, "repo_id": request.repo_id, "revision": request.revision},
        )


def test_download_api_accepts_provider(monkeypatch, tmp_path):
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
            "provider": "modelscope",
            "repo_id": "damo/model",
            "revision": "master",
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == "job-created"
    assert FakeDownloadManager.last_request.provider == "modelscope"
    assert FakeDownloadManager.last_request.repo_id == "damo/model"
    assert FakeDownloadManager.last_request.token is None
