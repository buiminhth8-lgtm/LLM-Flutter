"""Async wrappers for synchronous work."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import partial
from typing import TypeVar

T = TypeVar("T")


async def run_blocking_io(func: Callable[..., T], *args, **kwargs) -> T:
    return await asyncio.to_thread(partial(func, *args, **kwargs))


async def run_cpu_bound(func: Callable[..., T], *args, **kwargs) -> T:
    return await asyncio.to_thread(partial(func, *args, **kwargs))
