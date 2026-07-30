import time
from pathlib import Path

from llm_studio.downloads import (
    DownloadManager,
    DownloadProgressTracker,
    DownloadRequest,
    DownloadTaskState,
    RemoteFile,
)
from llm_studio.downloads.providers.modelscope import ModelScopeDownloadProvider
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
            "storage": {
                "trash_dir": str(root / "trash"),
                "jobs_dir": str(root / "jobs"),
            },
            "downloads": {
                "default_provider": "modelscope",
                "providers": {
                    "modelscope": {
                        "cache_dir": str(root / "ms-cache"),
                        "endpoint": "https://modelscope.cn",
                    }
                },
            },
            "external_models": [],
        }

    def get(self, key, default=None):
        return self._data.get(key, default)


class FakeModelScopeClient:
    def __init__(self):
        self.list_files_called = False
        self.snapshot_local_files_only = None

    def list_files(self, request):
        self.list_files_called = True
        return [RemoteFile("config.json", None), RemoteFile("model.safetensors", None)]

    def download_file(self, request, file, *, local_dir, cache_dir=None):
        target = local_dir / file.path
        target.parent.mkdir(parents=True, exist_ok=True)
        if file.path == "config.json":
            target.write_text('{"model_type":"llama"}', encoding="utf-8")
        else:
            target.write_bytes(b"12345")
        return target

    def snapshot_download(self, request, *, local_dir, cache_dir=None):
        self.snapshot_local_files_only = request.local_files_only
        local_dir.mkdir(parents=True, exist_ok=True)
        (local_dir / "config.json").write_text('{"model_type":"llama"}', encoding="utf-8")
        (local_dir / "model.safetensors").write_bytes(b"12345")
        return local_dir


class FailingModelScopeClient(FakeModelScopeClient):
    def list_files(self, request):
        raise RuntimeError("boom Authorization: Bearer ms_secret token=ms_secret")


class ListRepoOnlyHubApi:
    def __init__(self):
        self.calls = []

    def list_repo_files(self, repo_id, repo_type, *, revision=None, recursive=True):
        self.calls.append(
            {
                "repo_id": repo_id,
                "repo_type": repo_type,
                "revision": revision,
                "recursive": recursive,
            }
        )
        return [
            type("FileInfo", (), {"path": "config.json", "size": 23})(),
            type("FileInfo", (), {"path": "model.safetensors", "size": None})(),
        ]


class DownloadRepoWithProgressApi:
    def __init__(self, target: Path):
        self.target = target
        self.progress_callbacks = None

    def download_repo(
        self,
        repo_id,
        repo_type,
        *,
        revision=None,
        cache_dir=None,
        local_dir=None,
        allow_patterns=None,
        ignore_patterns=None,
        local_files_only=False,
        progress_callbacks=None,
    ):
        self.progress_callbacks = progress_callbacks
        target = Path(local_dir or self.target)
        target.mkdir(parents=True, exist_ok=True)
        callback = progress_callbacks[0]("model.safetensors", 10)
        callback.update(4)
        callback.update(6)
        callback.end()
        (target / "config.json").write_text('{"model_type":"llama"}', encoding="utf-8")
        (target / "model.safetensors").write_bytes(b"1234567890")
        return target


class DownloadRepoWithoutProgressApi:
    def __init__(self, target: Path):
        self.target = target

    def download_repo(
        self,
        repo_id,
        repo_type,
        *,
        revision=None,
        cache_dir=None,
        local_dir=None,
        allow_patterns=None,
        ignore_patterns=None,
        local_files_only=False,
    ):
        target = Path(local_dir or self.target)
        target.mkdir(parents=True, exist_ok=True)
        (target / "config.json").write_text('{"model_type":"llama"}', encoding="utf-8")
        return target


def _manager(tmp_path, client):
    repo = JobRepository(tmp_path / "jobs.sqlite")
    queue = JobQueue(repo)
    manager = DownloadManager(
        TinyConfig(tmp_path),
        queue,
        modelscope_client=client,
    )
    return manager, repo, queue


def _wait_for_terminal(repo: JobRepository, job_id: str):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        job = repo.get(job_id)
        if job.status in {JobStatus.SUCCEEDED.value, JobStatus.FAILED.value, JobStatus.CANCELLED.value}:
            return job
        time.sleep(0.01)
    raise AssertionError(f"job {job_id} did not finish")


def test_modelscope_download_registers_model_and_keeps_unknown_percent(tmp_path):
    manager, repo, queue = _manager(tmp_path, FakeModelScopeClient())

    job = manager.create_download(DownloadRequest(provider="modelscope", repo_id="damo/model"))
    queue.shutdown(wait=True)

    stored = repo.get(job.id)
    state = DownloadTaskState.from_job(stored)
    assert stored.status == JobStatus.SUCCEEDED.value
    assert state.provider == "modelscope"
    assert state.total_bytes is None
    assert state.percent is None
    assert state.registration_status == "succeeded"
    assert state.model_id


def test_modelscope_local_files_only_does_not_resolve_remote_files(tmp_path):
    fake = FakeModelScopeClient()
    manager, repo, queue = _manager(tmp_path, fake)

    job = manager.create_download(
        DownloadRequest(provider="modelscope", repo_id="damo/model", local_files_only=True)
    )
    queue.shutdown(wait=True)

    state = DownloadTaskState.from_job(repo.get(job.id))
    assert fake.list_files_called is False
    assert fake.snapshot_local_files_only is True
    assert state.provider == "modelscope"
    assert state.total_bytes is None
    assert state.percent is None


def test_modelscope_error_message_is_redacted(monkeypatch, tmp_path):
    monkeypatch.setenv("MODELSCOPE_API_TOKEN", "ms_secret")
    manager, repo, queue = _manager(tmp_path, FailingModelScopeClient())

    job = manager.create_download(DownloadRequest(provider="modelscope", repo_id="damo/model"))
    queue.shutdown(wait=True)

    stored = repo.get(job.id)
    assert stored.status == JobStatus.FAILED.value
    assert "ms_secret" not in (stored.error_message or "")
    assert "token=<redacted>" in (stored.error_message or "")


def test_modelscope_provider_maps_local_cache_error():
    provider = ModelScopeDownloadProvider(TinyConfig(Path(".")), client=None)

    error = provider._map_modelscope_error(RuntimeError("missing cache token=ms_secret"))

    assert error.error_code == "MODELSCOPE_LOCAL_FILES_NOT_FOUND"


def test_modelscope_provider_supports_list_repo_files_without_get_model_files():
    provider = ModelScopeDownloadProvider(TinyConfig(Path(".")), client=None)
    api = ListRepoOnlyHubApi()

    list_func = provider._repo_file_list_func(api)
    raw_files = provider._call_supported_kwargs(
        list_func,
        model_id="damo/model",
        repo_id="damo/model",
        repo_type="model",
        revision="master",
        recursive=True,
    )

    assert api.calls == [
        {
            "repo_id": "damo/model",
            "repo_type": "model",
            "revision": "master",
            "recursive": True,
        }
    ]
    assert [item.path for item in raw_files] == ["config.json", "model.safetensors"]


def test_modelscope_download_repo_progress_callback_flushes(monkeypatch, tmp_path):
    provider = ModelScopeDownloadProvider(TinyConfig(tmp_path), client=None)
    api = DownloadRepoWithProgressApi(tmp_path / "download")
    monkeypatch.setattr(provider, "_create_hub_api", lambda cls: api)
    tracker = DownloadProgressTracker([RemoteFile("model.safetensors", 10)])
    snapshots = []

    result = provider.download_snapshot(
        DownloadRequest(provider="modelscope", repo_id="damo/model"),
        tmp_path / "target",
        tracker,
        on_progress=snapshots.append,
    )

    assert result == tmp_path / "target"
    assert api.progress_callbacks
    assert snapshots[-1].downloaded_bytes == 10
    assert snapshots[-1].total_bytes == 10
    assert snapshots[-1].current_file == "model.safetensors"


def test_modelscope_download_repo_without_progress_callback_support_does_not_fail(monkeypatch, tmp_path):
    provider = ModelScopeDownloadProvider(TinyConfig(tmp_path), client=None)
    api = DownloadRepoWithoutProgressApi(tmp_path / "download")
    monkeypatch.setattr(provider, "_create_hub_api", lambda cls: api)
    tracker = DownloadProgressTracker([RemoteFile("config.json", None)])

    result = provider.download_snapshot(
        DownloadRequest(provider="modelscope", repo_id="damo/model"),
        tmp_path / "target",
        tracker,
        on_progress=lambda snapshot: None,
    )

    assert result == tmp_path / "target"
    assert (tmp_path / "target" / "config.json").exists()
