import asyncio

import pytest

from llm_studio.runtime.gpu_scheduler import (
    GpuTaskRequest,
    GpuTaskScheduler,
    GpuTaskTimeoutError,
    GpuTaskType,
)


@pytest.mark.anyio
async def test_gpu_scheduler_allows_only_one_heavy_task():
    scheduler = GpuTaskScheduler(max_heavy_tasks=1, queue_timeout_seconds=0.1)

    async with scheduler.acquire(GpuTaskRequest(GpuTaskType.INFERENCE, "chat", "r1")):
        snapshot = scheduler.snapshot()
        assert snapshot.running[0]["task_type"] == "inference"
        with pytest.raises(GpuTaskTimeoutError):
            async with scheduler.acquire(
                GpuTaskRequest(GpuTaskType.BENCHMARK, "benchmark", "r2", timeout_seconds=0.1)
            ):
                pass

    assert scheduler.snapshot().running == ()


@pytest.mark.anyio
async def test_gpu_scheduler_releases_after_exception():
    scheduler = GpuTaskScheduler(max_heavy_tasks=1, queue_timeout_seconds=0.1)

    with pytest.raises(RuntimeError):
        async with scheduler.acquire(GpuTaskRequest(GpuTaskType.MODEL_LOAD, "load", "r1")):
            raise RuntimeError("boom")

    async with scheduler.acquire(GpuTaskRequest(GpuTaskType.INFERENCE, "chat", "r2")):
        assert len(scheduler.snapshot().running) == 1


@pytest.mark.anyio
async def test_gpu_scheduler_disabled_does_not_block():
    scheduler = GpuTaskScheduler(enabled=False, max_heavy_tasks=1)

    async with scheduler.acquire(GpuTaskRequest(GpuTaskType.INFERENCE, "a")):
        async with scheduler.acquire(GpuTaskRequest(GpuTaskType.BENCHMARK, "b")):
            await asyncio.sleep(0)

    assert scheduler.snapshot().running == ()
