"""Download request and progress entities."""

from __future__ import annotations

from dataclasses import dataclass

from llm_studio.jobs import Job, JobStatus


@dataclass(frozen=True)
class DownloadRequest:
    repo_id: str
    revision: str | None = None
    allow_patterns: tuple[str, ...] | None = None
    ignore_patterns: tuple[str, ...] | None = None
    local_name: str | None = None
    token: str | None = None
    local_files_only: bool = False


@dataclass(frozen=True)
class DownloadProgress:
    downloaded_bytes: int
    total_bytes: int | None
    completed_files: int
    total_files: int | None
    speed_bytes_per_second: float | None
    eta_seconds: float | None
    current_file: str | None

    def as_fraction(self) -> float | None:
        if self.total_bytes and self.total_bytes > 0:
            return min(1.0, self.downloaded_bytes / self.total_bytes)
        if self.total_files and self.total_files > 0:
            return min(1.0, self.completed_files / self.total_files)
        return None


@dataclass(frozen=True)
class DownloadTaskState:
    job_id: str
    repo_id: str
    revision: str | None
    status: str
    downloaded_bytes: int | None
    total_bytes: int | None
    completed_files: int | None
    total_files: int | None
    speed_bytes_per_second: float | None
    eta_seconds: float | None
    current_file: str | None
    can_cancel: bool
    can_retry: bool
    resume_supported: bool
    message: str | None
    error_code: str | None
    error_message: str | None
    model_id: str | None

    @classmethod
    def from_job(cls, job: Job) -> DownloadTaskState:
        payload = job.payload
        status = job.status
        can_cancel = status in {JobStatus.PENDING.value, JobStatus.RUNNING.value}
        can_retry = status in {
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
            JobStatus.INTERRUPTED.value,
        }
        return cls(
            job_id=job.id,
            repo_id=str(payload.get("repo_id", "")),
            revision=payload.get("revision"),
            status=status,
            downloaded_bytes=payload.get("downloaded_bytes"),
            total_bytes=payload.get("total_bytes"),
            completed_files=payload.get("completed_files"),
            total_files=payload.get("total_files"),
            speed_bytes_per_second=payload.get("speed_bytes_per_second"),
            eta_seconds=payload.get("eta_seconds"),
            current_file=payload.get("current_file"),
            can_cancel=can_cancel,
            can_retry=can_retry,
            resume_supported=True,
            message=job.message,
            error_code=job.error_code,
            error_message=job.error_message,
            model_id=payload.get("model_id"),
        )

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()
