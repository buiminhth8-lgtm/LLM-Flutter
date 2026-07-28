"""Async concurrency controls for local model loading and inference."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager


class QueueFullError(RuntimeError):
    """Raised when inference queue capacity is exhausted."""


class ModelConcurrencyController:
    def __init__(
        self,
        max_inference_concurrency: int = 1,
        max_queue_size: int = 8,
    ):
        self.max_inference_concurrency = max(1, max_inference_concurrency)
        self.max_queue_size = max(0, max_queue_size)
        self._load_lock = asyncio.Lock()
        self._inference_semaphore = asyncio.Semaphore(self.max_inference_concurrency)
        self._queued = 0
        self._queue_lock = asyncio.Lock()

    @property
    def queue_size(self) -> int:
        return self._queued

    @property
    def is_loading_locked(self) -> bool:
        return self._load_lock.locked()

    @asynccontextmanager
    async def model_load(self):
        async with self._load_lock:
            yield

    @asynccontextmanager
    async def model_unload(self):
        async with self._load_lock:
            yield

    @asynccontextmanager
    async def inference(self, wait_timeout_seconds: float | None = None):
        async with self._queue_lock:
            if self._queued >= self.max_queue_size:
                raise QueueFullError("推理队列已满，请稍后重试。")
            self._queued += 1
        try:
            if wait_timeout_seconds and wait_timeout_seconds > 0:
                await asyncio.wait_for(
                    self._inference_semaphore.acquire(),
                    timeout=wait_timeout_seconds,
                )
            else:
                await self._inference_semaphore.acquire()
            try:
                yield
            finally:
                self._inference_semaphore.release()
        except TimeoutError as exc:
            raise TimeoutError("等待推理队列超时。") from exc
        finally:
            async with self._queue_lock:
                self._queued = max(0, self._queued - 1)
