"""Model download manager with background job integration."""

from __future__ import annotations

import threading
from pathlib import Path

from llm_studio.jobs import Job, JobQueue, JobType
from llm_studio.jobs.exceptions import JobCancelledError
from llm_studio.models.repository import LocalModelRepository
from llm_studio.models.storage import (
    atomic_replace_directory,
    disk_free_bytes,
    layout_from_config,
    sanitize_local_name,
)

from .entities import DownloadProgress, DownloadRequest
from .exceptions import DiskSpaceError, DownloadValidationError
from .huggingface_client import HuggingFaceDownloadClient
from .validation import validate_downloaded_model


class DownloadManager:
    def __init__(
        self,
        config,
        job_queue: JobQueue,
        hf_client: HuggingFaceDownloadClient | None = None,
        model_repository: LocalModelRepository | None = None,
    ):
        self.config = config
        self.layout = layout_from_config(config)
        self.layout.ensure()
        self.job_queue = job_queue
        self.hf_client = hf_client or HuggingFaceDownloadClient()
        self.model_repository = model_repository or LocalModelRepository(config, self.layout)

    def create_download(self, request: DownloadRequest) -> Job:
        local_name = sanitize_local_name(request.local_name or request.repo_id.replace("/", "--"))
        payload = {
            "repo_id": request.repo_id,
            "revision": request.revision,
            "allow_patterns": list(request.allow_patterns or ()),
            "ignore_patterns": list(request.ignore_patterns or ()),
            "local_name": local_name,
            "local_files_only": request.local_files_only,
        }
        return self.job_queue.submit(
            JobType.MODEL_DOWNLOAD.value,
            payload,
            lambda job, update, cancel: self._run_download(job, request, update, cancel),
        )

    def cancel_job(self, job_id: str) -> Job:
        return self.job_queue.cancel(job_id)

    def retry_interrupted(self, job: Job) -> Job:
        payload = job.payload
        return self.create_download(
            DownloadRequest(
                repo_id=str(payload["repo_id"]),
                revision=payload.get("revision"),
                allow_patterns=tuple(payload.get("allow_patterns") or ()) or None,
                ignore_patterns=tuple(payload.get("ignore_patterns") or ()) or None,
                local_name=str(payload.get("local_name") or ""),
                token=None,
                local_files_only=bool(payload.get("local_files_only", False)),
            )
        )

    def _run_download(self, job: Job, request: DownloadRequest, update, cancel_flag: threading.Event) -> None:
        local_name = sanitize_local_name(str(job.payload["local_name"]))
        if disk_free_bytes(self.layout.temp_dir) < self.layout.minimum_free_space_gb * 1024**3:
            raise DiskSpaceError(f"可用磁盘空间不足 {self.layout.minimum_free_space_gb}GB。")

        temp_dir = self.layout.temp_dir / f"{job.id}-{local_name}"
        final_dir = self.layout.root_dir / "transformers" / local_name
        if final_dir.exists():
            raise DownloadValidationError(f"目标模型已存在，拒绝覆盖: {final_dir}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        update(0.0, "开始下载；取消后重新开始会利用 Hugging Face 缓存续传。")
        if cancel_flag.is_set():
            raise JobCancelledError("下载已取消。")

        self.hf_client.snapshot_download(
            request,
            local_dir=temp_dir,
            cache_dir=Path(self.config.get("huggingface", {}).get("cache_dir", self.layout.temp_dir / "hf-cache")),
        )
        progress = self._scan_progress(temp_dir)
        update(progress.as_fraction(), "下载完成，正在校验模型文件。")
        if cancel_flag.is_set():
            raise JobCancelledError("下载已取消。")

        validate_downloaded_model(temp_dir)
        atomic_replace_directory(temp_dir, final_dir)
        self.model_repository.scan()
        update(1.0, f"模型已注册: {final_dir}")

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
