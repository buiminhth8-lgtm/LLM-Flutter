"""Unified scheduling for GPU-heavy tasks."""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Iterator
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import StrEnum


class GpuTaskType(StrEnum):
    INFERENCE = "inference"
    MODEL_LOAD = "model_load"
    MODEL_UNLOAD = "model_unload"
    BENCHMARK = "benchmark"
    VISION = "vision"
    FINETUNE = "finetune"
    LORA_MERGE = "lora_merge"


@dataclass(frozen=True)
class GpuTaskRequest:
    task_type: GpuTaskType
    owner: str
    request_id: str | None = None
    timeout_seconds: float | None = None


@dataclass(frozen=True)
class GpuSchedulerSnapshot:
    enabled: bool
    max_heavy_tasks: int
    running: tuple[dict[str, object], ...]
    queued_count: int

    def to_dict(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "max_heavy_tasks": self.max_heavy_tasks,
            "running": list(self.running),
            "queued_count": self.queued_count,
        }


class GpuTaskTimeoutError(RuntimeError):
    """Raised when a GPU task cannot acquire the scheduler in time."""


class GpuTaskScheduler:
    def __init__(
        self,
        *,
        enabled: bool = True,
        max_heavy_tasks: int = 1,
        queue_timeout_seconds: float = 30,
    ):
        self.enabled = enabled
        self.max_heavy_tasks = max(1, int(max_heavy_tasks))
        self.queue_timeout_seconds = max(0.1, float(queue_timeout_seconds))
        self._semaphore = threading.BoundedSemaphore(self.max_heavy_tasks)
        self._lock = threading.Lock()
        self._running: list[dict[str, object]] = []
        self._queued_count = 0

    def snapshot(self) -> GpuSchedulerSnapshot:
        with self._lock:
            return GpuSchedulerSnapshot(
                enabled=self.enabled,
                max_heavy_tasks=self.max_heavy_tasks,
                running=tuple(dict(item) for item in self._running),
                queued_count=self._queued_count,
            )

    @asynccontextmanager
    async def acquire(self, request: GpuTaskRequest):
        token = await asyncio.to_thread(self._acquire_sync, request)
        try:
            yield
        finally:
            await asyncio.to_thread(self._release_sync, token)

    @contextmanager
    def acquire_sync(self, request: GpuTaskRequest) -> Iterator[None]:
        token = self._acquire_sync(request)
        try:
            yield
        finally:
            self._release_sync(token)

    def _acquire_sync(self, request: GpuTaskRequest) -> dict[str, object] | None:
        if not self.enabled:
            return None
        timeout = request.timeout_seconds
        if timeout is None:
            timeout = self.queue_timeout_seconds
        with self._lock:
            self._queued_count += 1
        acquired = False
        try:
            acquired = self._semaphore.acquire(timeout=max(0.1, timeout))
            if not acquired:
                raise GpuTaskTimeoutError("GPU 正在执行其他任务，请稍后重试。")
            token = {
                "task_type": request.task_type.value,
                "owner": request.owner,
                "request_id": request.request_id,
                "started_at": time.time(),
            }
            with self._lock:
                self._running.append(token)
            print(
                f"[GPU] task-start type={request.task_type.value} "
                f"owner={request.owner} request_id={request.request_id or '-'}"
            )
            return token
        finally:
            with self._lock:
                self._queued_count = max(0, self._queued_count - 1)
            if not acquired:
                print(
                    f"[GPU] task-timeout type={request.task_type.value} "
                    f"owner={request.owner} request_id={request.request_id or '-'}"
                )

    def _release_sync(self, token: dict[str, object] | None) -> None:
        if not self.enabled or token is None:
            return
        with self._lock:
            self._running = [item for item in self._running if item is not token]
        self._semaphore.release()
        print(
            f"[GPU] task-end type={token.get('task_type')} "
            f"owner={token.get('owner')} request_id={token.get('request_id') or '-'}"
        )
