"""Model download manager with background job integration."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from llm_studio.jobs import Job, JobQueue, JobStatus, JobType
from llm_studio.jobs.exceptions import JobCancelNotAllowedError
from llm_studio.models.entities import ModelStatus
from llm_studio.models.repository import LocalModelRepository
from llm_studio.models.storage import (
    atomic_replace_directory,
    disk_free_bytes,
    layout_from_config,
    sanitize_local_name,
)

from .entities import DownloadProgress, DownloadRequest
from .exceptions import (
    DiskSpaceError,
    DownloadAlreadyRunningError,
    DownloadCancelledError,
    DownloadCancelNotAllowedError,
    DownloadModelScanError,
    DownloadModelUnsupportedError,
    DownloadRetryNotAllowedError,
    DownloadValidationError,
)
from .huggingface_client import HuggingFaceDownloadClient
from .progress import DownloadProgressTracker, RemoteFile
from .providers.base import DownloadProvider
from .providers.registry import get_download_provider
from .validation import validate_downloaded_model

ACTIVE_DOWNLOAD_STATUSES = {
    JobStatus.PENDING.value,
    JobStatus.RUNNING.value,
    JobStatus.CANCELLING.value,
}


class DownloadManager:
    def __init__(
        self,
        config,
        job_queue: JobQueue,
        hf_client: HuggingFaceDownloadClient | None = None,
        modelscope_client: Any | None = None,
        providers: dict[str, DownloadProvider] | None = None,
        model_repository: LocalModelRepository | None = None,
    ):
        self.config = config
        self.layout = layout_from_config(config)
        self.layout.ensure()
        self.job_queue = job_queue
        self.hf_client = hf_client or HuggingFaceDownloadClient()
        self.modelscope_client = modelscope_client
        self.providers = providers or {}
        self.model_repository = model_repository or LocalModelRepository(config, self.layout)

    def create_download(self, request: DownloadRequest, *, parent_job_id: str | None = None) -> Job:
        request = self._with_default_provider(request)
        self._ensure_not_already_running(request)
        local_name = sanitize_local_name(request.local_name or request.repo_id.replace("/", "--"))
        payload = {
            "provider": request.provider,
            "repo_id": request.repo_id,
            "revision": request.revision,
            "allow_patterns": list(request.allow_patterns or ()),
            "ignore_patterns": list(request.ignore_patterns or ()),
            "local_name": local_name,
            "local_files_only": request.local_files_only,
            "downloaded_bytes": None,
            "total_bytes": None,
            "percent": None,
            "completed_files": None,
            "total_files": None,
            "speed_bytes_per_second": None,
            "eta_seconds": None,
            "current_file": None,
            "cancel_requested": False,
            "resume_supported": True,
            "registration_status": None,
            "model_id": None,
            "parent_job_id": parent_job_id,
        }
        return self.job_queue.submit(
            JobType.MODEL_DOWNLOAD.value,
            payload,
            lambda job, update, cancel: self._run_download(job, request, cancel),
        )

    def cancel_job(self, job_id: str) -> Job:
        try:
            job = self.job_queue.cancel(job_id)
        except JobCancelNotAllowedError as exc:
            raise DownloadCancelNotAllowedError("该下载任务当前不能取消。") from exc
        self._merge_payload(
            job.id,
            {"cancel_requested": True},
            message="取消请求已提交；当前文件传输可能完成后才会停止。",
        )
        return self.job_queue.repository.get(job.id)

    def retry_interrupted(self, job: Job) -> Job:
        if job.status not in {
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
            JobStatus.INTERRUPTED.value,
        }:
            raise DownloadRetryNotAllowedError("只有失败、取消或中断的下载任务可以重试。")
        payload = job.payload
        return self.create_download(
            DownloadRequest(
                repo_id=str(payload["repo_id"]),
                provider=str(payload.get("provider") or self._default_provider_name()),
                revision=payload.get("revision"),
                allow_patterns=tuple(payload.get("allow_patterns") or ()) or None,
                ignore_patterns=tuple(payload.get("ignore_patterns") or ()) or None,
                local_name=str(payload.get("local_name") or ""),
                token=None,
                local_files_only=bool(payload.get("local_files_only", False)),
            ),
            parent_job_id=job.id,
        )

    def _run_download(self, job: Job, request: DownloadRequest, cancel_flag: threading.Event) -> None:
        request = self._with_default_provider(request)
        provider = self._provider_for(request)
        local_name = sanitize_local_name(str(job.payload["local_name"]))
        if disk_free_bytes(self.layout.temp_dir) < self.layout.minimum_free_space_gb * 1024**3:
            raise DiskSpaceError(f"可用磁盘空间不足 {self.layout.minimum_free_space_gb}GB。")

        temp_dir = self.layout.temp_dir / f"{job.id}-{local_name}"
        final_dir = self.layout.root_dir / "transformers" / local_name
        self._merge_payload(job.id, {"temp_dir": str(temp_dir), "download_temp_dir": str(temp_dir)})
        if final_dir.exists():
            raise DownloadValidationError(f"目标模型已存在，拒绝覆盖: {final_dir}")
        temp_dir.mkdir(parents=True, exist_ok=True)

        files = [] if request.local_files_only else self._list_files(provider, request)
        tracker = DownloadProgressTracker(files)
        self._publish_progress(
            job.id,
            tracker.snapshot(),
            f"开始下载；重试会复用 {self._provider_label(request.provider)} 缓存。",
        )
        self._raise_if_cancelled(job.id, cancel_flag, request.provider)

        final_progress: DownloadProgress
        if files:
            for remote_file in files:
                self._publish_progress(job.id, tracker.start_file(remote_file.path), f"正在下载 {remote_file.path}")
                self._raise_if_cancelled(job.id, cancel_flag, request.provider)
                downloaded_path = self._download_file(provider, request, remote_file, temp_dir)
                observed_size = self._file_size(downloaded_path)
                progress = tracker.complete_file(remote_file.path, size_bytes=remote_file.size or observed_size)
                self._publish_progress(job.id, progress, f"已完成 {remote_file.path}")
                self._raise_if_cancelled(job.id, cancel_flag, request.provider)
            final_progress = tracker.snapshot()
        else:
            provider.download_snapshot(request, temp_dir, tracker, cancel_flag)
            final_progress = self._scan_progress(temp_dir)
            self._publish_progress(job.id, final_progress, "文件清单不可用，已根据本地文件扫描更新进度。")
            self._raise_if_cancelled(job.id, cancel_flag, request.provider)

        self._publish_progress(job.id, final_progress, "下载完成，正在校验模型文件。")
        self._raise_if_cancelled(job.id, cancel_flag, request.provider)

        validate_downloaded_model(temp_dir)
        atomic_replace_directory(temp_dir, final_dir)
        self._register_downloaded_model(job.id, final_dir)

    def _ensure_not_already_running(self, request: DownloadRequest) -> None:
        for job in self.job_queue.repository.list(limit=200):
            if job.type != JobType.MODEL_DOWNLOAD.value or job.status not in ACTIVE_DOWNLOAD_STATUSES:
                continue
            payload = job.payload
            if (
                payload.get("provider") == request.provider
                and payload.get("repo_id") == request.repo_id
                and payload.get("revision") == request.revision
            ):
                raise DownloadAlreadyRunningError("同一下载源、仓库和 revision 已有下载任务正在运行。")

    def _list_files(self, provider: DownloadProvider, request: DownloadRequest) -> list[RemoteFile]:
        return provider.resolve_files(request)

    def _download_file(
        self,
        provider: DownloadProvider,
        request: DownloadRequest,
        remote_file: RemoteFile,
        temp_dir: Path,
    ) -> Path:
        return provider.download_file(request, remote_file, local_dir=temp_dir)

    def _register_downloaded_model(self, job_id: str, final_dir: Path) -> None:
        self._merge_payload(job_id, {"registration_status": "scanning"}, message="下载完成，正在扫描模型仓库。")
        models = self.model_repository.scan()
        model = next((item for item in models if item.path == final_dir.resolve()), None)
        if model is None:
            self._merge_payload(job_id, {"registration_status": "failed"}, message="下载成功，但模型扫描未识别该目录。")
            raise DownloadModelScanError("下载成功，但模型扫描未识别该目录。")
        if model.status != ModelStatus.READY:
            self._merge_payload(
                job_id,
                {"registration_status": "failed", "model_id": model.id},
                message="下载成功，但模型不是 ready 状态。",
            )
            raise DownloadModelUnsupportedError("下载成功，但模型不是 ready 状态。")
        self._merge_payload(
            job_id,
            {"registration_status": "succeeded", "model_id": model.id},
            progress=1.0,
            message=f"模型已注册: {model.id}",
        )

    def _publish_progress(self, job_id: str, progress: DownloadProgress, message: str) -> None:
        fraction = progress.as_fraction()
        percent = None
        if progress.total_bytes is not None and progress.total_bytes > 0:
            percent = min(100.0, max(0.0, progress.downloaded_bytes / progress.total_bytes * 100.0))
        self._merge_payload(
            job_id,
            {
                "downloaded_bytes": progress.downloaded_bytes,
                "total_bytes": progress.total_bytes,
                "percent": percent,
                "completed_files": progress.completed_files,
                "total_files": progress.total_files,
                "speed_bytes_per_second": progress.speed_bytes_per_second,
                "eta_seconds": progress.eta_seconds,
                "current_file": progress.current_file,
                "resume_supported": True,
            },
            progress=fraction,
            message=message,
        )

    def _raise_if_cancelled(
        self,
        job_id: str,
        cancel_flag: threading.Event,
        provider: str | None,
    ) -> None:
        if cancel_flag.is_set():
            self._merge_payload(
                job_id,
                {"cancel_requested": True},
                message=f"下载已取消；重试会复用 {self._provider_label(provider)} 缓存。",
            )
            raise DownloadCancelledError("下载已取消。")

    def _merge_payload(
        self,
        job_id: str,
        payload_update: dict[str, Any],
        *,
        progress: float | None = None,
        message: str | None = None,
    ) -> None:
        current = self.job_queue.repository.get(job_id)
        payload = {**current.payload, **payload_update}
        self.job_queue.repository.save(
            current.with_update(
                payload=payload,
                progress=current.progress if progress is None else progress,
                message=current.message if message is None else message,
            )
        )

    def _scan_progress(self, path: Path) -> DownloadProgress:
        downloaded = 0
        completed = 0
        for item in path.rglob("*"):
            if item.is_file():
                completed += 1
                downloaded += item.stat().st_size
        return DownloadProgress(
            downloaded_bytes=downloaded,
            total_bytes=None,
            completed_files=completed,
            total_files=None,
            speed_bytes_per_second=None,
            eta_seconds=None,
            current_file=None,
        )

    def _file_size(self, path: Path) -> int | None:
        try:
            return path.stat().st_size if path.exists() and path.is_file() else None
        except OSError:
            return None

    def _default_provider_name(self) -> str:
        downloads_cfg = self.config.get("downloads", {})
        if isinstance(downloads_cfg, dict):
            return str(downloads_cfg.get("default_provider") or "huggingface").strip().lower()
        return "huggingface"

    def _with_default_provider(self, request: DownloadRequest) -> DownloadRequest:
        if request.provider:
            return request
        return DownloadRequest(
            repo_id=request.repo_id,
            provider=self._default_provider_name(),
            revision=request.revision,
            allow_patterns=request.allow_patterns,
            ignore_patterns=request.ignore_patterns,
            local_name=request.local_name,
            token=request.token,
            local_files_only=request.local_files_only,
        )

    def _provider_for(self, request: DownloadRequest) -> DownloadProvider:
        name = str(request.provider or self._default_provider_name()).strip().lower()
        if name in self.providers:
            return self.providers[name]
        return get_download_provider(
            name,
            self.config,
            hf_client=self.hf_client,
            modelscope_client=self.modelscope_client,
        )

    def _provider_label(self, provider: str | None) -> str:
        return "ModelScope" if provider == "modelscope" else "Hugging Face"
