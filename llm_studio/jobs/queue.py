"""In-process background job queue."""

from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from llm_studio.security.redaction import redact_sensitive_text

from .entities import TERMINAL_JOB_STATUSES, Job, JobStatus, JobType, sanitize_payload
from .exceptions import JobCancelledError, JobCancelNotAllowedError, JobQueueClosedError
from .repository import JobRepository


class JobQueue:
    def __init__(self, repository: JobRepository):
        self.repository = repository
        self._closed = False
        self._lock = threading.Lock()
        self._executors = {
            JobType.MODEL_DOWNLOAD.value: ThreadPoolExecutor(max_workers=2, thread_name_prefix="model-download"),
            JobType.MODEL_SCAN.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="model-scan"),
            JobType.MODEL_DELETE.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="model-delete"),
            JobType.MODEL_VERIFY.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="model-verify"),
            JobType.BENCHMARK.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="benchmark"),
            JobType.LORA_MERGE.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="lora-merge"),
            JobType.RAG_REBUILD.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="rag-rebuild"),
            JobType.CACHE_CLEANUP.value: ThreadPoolExecutor(max_workers=1, thread_name_prefix="cache-cleanup"),
        }
        self._cancel_flags: dict[str, threading.Event] = {}

    def submit(
        self,
        job_type: str,
        payload: dict[str, Any],
        handler: Callable[[Job, Callable[[float | None, str | None], None], threading.Event], Any],
    ) -> Job:
        with self._lock:
            if self._closed:
                raise JobQueueClosedError("任务队列正在关闭，拒绝接收新任务。")
            job = Job.new(f"job-{uuid.uuid4().hex[:16]}", job_type, sanitize_payload(payload))
            self.repository.save(job)
            cancel_flag = threading.Event()
            self._cancel_flags[job.id] = cancel_flag

        executor = self._executors.get(job_type) or self._executors[JobType.MODEL_SCAN.value]
        executor.submit(self._run, job, handler, cancel_flag)
        return job

    def cancel(self, job_id: str) -> Job:
        job = self.repository.get(job_id)
        if job.status in TERMINAL_JOB_STATUSES:
            raise JobCancelNotAllowedError("????????????")
        flag = self._cancel_flags.get(job_id)
        if flag:
            flag.set()
        if job.status != JobStatus.CANCELLING.value:
            job = job.with_update(status=JobStatus.CANCELLING.value, message="???????")
            self.repository.save(job)
        return job

    def shutdown(self, *, wait: bool = True) -> None:
        with self._lock:
            self._closed = True
        if not wait:
            for flag in self._cancel_flags.values():
                flag.set()
        for executor in self._executors.values():
            executor.shutdown(wait=wait, cancel_futures=not wait)

    def _run(self, job: Job, handler, cancel_flag: threading.Event) -> None:
        job = job.with_update(
            status=JobStatus.RUNNING.value,
            started_at=datetime.now(timezone.utc),
            message="任务开始执行。",
        )
        self.repository.save(job)

        def update(progress: float | None, message: str | None = None) -> None:
            current = self.repository.get(job.id)
            if cancel_flag.is_set():
                raise JobCancelledError("任务已取消。")
            self.repository.save(current.with_update(progress=progress, message=message))

        try:
            handler(job, update, cancel_flag)
        except JobCancelledError as exc:
            current = self.repository.get(job.id)
            self.repository.save(
                current.with_update(
                    status=JobStatus.CANCELLED.value,
                    finished_at=datetime.now(timezone.utc),
                    error_code=getattr(exc, "error_code", "JOB_CANCELLED"),
                    error_message=redact_sensitive_text(str(exc)),
                    message="任务已取消。",
                )
            )
        except Exception as exc:
            current = self.repository.get(job.id)
            self.repository.save(
                current.with_update(
                    status=JobStatus.FAILED.value,
                    finished_at=datetime.now(timezone.utc),
                    error_code=getattr(exc, "error_code", type(exc).__name__),
                    error_message=redact_sensitive_text(str(exc)),
                    message="任务失败。",
                )
            )
        else:
            current = self.repository.get(job.id)
            self.repository.save(
                current.with_update(
                    status=JobStatus.SUCCEEDED.value,
                    progress=1.0,
                    finished_at=datetime.now(timezone.utc),
                    message="任务完成。",
                )
            )
        finally:
            self._cancel_flags.pop(job.id, None)
