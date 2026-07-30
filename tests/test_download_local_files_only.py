from pathlib import Path

from llm_studio.downloads import DownloadManager, DownloadRequest, DownloadTaskState
from llm_studio.downloads.exceptions import DownloadLocalFilesNotFoundError
from llm_studio.jobs import JobQueue, JobRepository, JobStatus


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
            "storage": {"trash_dir": str(root / "trash"), "jobs_dir": str(root / "jobs")},
            "downloads": {
                "default_provider": "modelscope",
                "providers": {"modelscope": {"cache_dir": str(root / "ms-cache")}},
            },
            "external_models": [],
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class LocalOnlyClient:
    def __init__(self, *, missing: bool = False):
        self.missing = missing
        self.list_files_called = False
        self.snapshot_local_files_only = None

    def list_files(self, request):
        self.list_files_called = True
        raise AssertionError("local_files_only=True must not call remote metadata APIs")

    def snapshot_download(self, request, *, local_dir, cache_dir=None):
        self.snapshot_local_files_only = request.local_files_only
        if self.missing:
            raise DownloadLocalFilesNotFoundError("local cache missing")
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "config.json").write_text('{"model_type":"llama"}', encoding="utf-8")
        (local_dir / "model.safetensors").write_bytes(b"12345")
        return local_dir


def _manager(tmp_path, modelscope_client):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    return DownloadManager(TinyConfig(tmp_path), queue, modelscope_client=modelscope_client), repo, queue


def test_local_files_only_does_not_call_remote_metadata_api(tmp_path):
    modelscope_client = LocalOnlyClient()
    manager, repo, queue = _manager(tmp_path, modelscope_client)

    job = manager.create_download(DownloadRequest(repo_id="org/model", local_files_only=True))
    queue.shutdown(wait=True)

    state = DownloadTaskState.from_job(repo.get(job.id))
    assert modelscope_client.list_files_called is False
    assert modelscope_client.snapshot_local_files_only is True
    assert state.status == JobStatus.SUCCEEDED.value
    assert state.provider == "modelscope"
    assert state.total_bytes is None
    assert state.percent is None


def test_local_files_only_missing_cache_returns_stable_error(tmp_path):
    modelscope_client = LocalOnlyClient(missing=True)
    manager, repo, queue = _manager(tmp_path, modelscope_client)

    job = manager.create_download(DownloadRequest(repo_id="org/model", local_files_only=True))
    queue.shutdown(wait=True)

    stored = repo.get(job.id)
    assert modelscope_client.list_files_called is False
    assert modelscope_client.snapshot_local_files_only is True
    assert stored.status == JobStatus.FAILED.value
    assert stored.error_code == "DOWNLOAD_LOCAL_FILES_NOT_FOUND"
