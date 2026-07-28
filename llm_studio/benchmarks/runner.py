"""Benchmark runner."""

from __future__ import annotations

import random
import time
import uuid
from collections.abc import Callable

from llm_studio.generation import GenerationConfig
from llm_studio.runtime.capabilities import detect_runtime_capabilities

from .entities import BenchmarkConfig, BenchmarkResult, BenchmarkRun
from .metrics import cuda_peak_memory, reset_cuda_peak_memory, sync_cuda, tokens_per_second
from .prompts import get_prompt_set
from .repository import BenchmarkRepository


class BenchmarkRunner:
    def __init__(self, config, runner_factory: Callable[[str], object], repository: BenchmarkRepository | None = None):
        self.config = config
        self.runner_factory = runner_factory
        self.repository = repository or BenchmarkRepository(config)

    def run(self, benchmark_config: BenchmarkConfig) -> BenchmarkResult:
        self._seed_everything(benchmark_config.seed)
        caps = detect_runtime_capabilities(run_bnb_probe=False)
        environment = {
            "python": caps.python_version,
            "torch": caps.torch_version,
            "cuda": caps.cuda_runtime,
            "gpu": caps.gpu_name,
            "bf16_supported": caps.bf16_supported,
        }
        prompts = get_prompt_set(benchmark_config.prompt_set)
        runs: list[BenchmarkRun] = []
        runner = self.runner_factory(benchmark_config.model_id)
        load_start = time.perf_counter()
        if hasattr(runner, "load"):
            runner.load()
        if benchmark_config.adapter_id:
            self._apply_adapter(runner, benchmark_config.adapter_id)
        sync_cuda()
        load_time = time.perf_counter() - load_start

        try:
            total_runs = benchmark_config.warmup_runs + benchmark_config.measured_runs
            for idx in range(total_runs):
                context_length = benchmark_config.context_lengths[idx % len(benchmark_config.context_lengths)]
                prompt = self._fit_prompt(runner, prompts[idx % len(prompts)], context_length)
                measured = idx >= benchmark_config.warmup_runs
                run = self._run_once(runner, prompt, benchmark_config, load_time if measured and not runs else None)
                if measured:
                    runs.append(run)
        finally:
            if hasattr(runner, "unload"):
                runner.unload()
        result = BenchmarkResult.now(f"bench-{uuid.uuid4().hex[:12]}", benchmark_config, environment, runs)
        self.repository.save(result)
        return result

    def _run_once(self, runner, prompt: str, config: BenchmarkConfig, load_time: float | None) -> BenchmarkRun:
        generation_config = GenerationConfig(max_new_tokens=config.max_new_tokens, do_sample=False)
        sync_cuda()
        reset_cuda_peak_memory()
        start = time.perf_counter()
        first_token_time: float | None = None
        output = ""
        try:
            for token in runner.generate_stream([{"role": "user", "content": prompt}], generation_config=generation_config):
                if first_token_time is None:
                    sync_cuda()
                    first_token_time = time.perf_counter()
                output += token
            sync_cuda()
            total = time.perf_counter() - start
            ttft = first_token_time - start if first_token_time else None
            out_tokens = self._count_tokens(runner, output)
            peak_allocated, peak_reserved = cuda_peak_memory()
            return BenchmarkRun(
                input_tokens=self._count_tokens(runner, prompt),
                output_tokens=out_tokens,
                load_time_seconds=load_time,
                tokenizer_load_time_seconds=None,
                ttft_seconds=ttft,
                generation_seconds=total,
                tokens_per_second=tokens_per_second(out_tokens, ttft, total),
                peak_cuda_allocated_bytes=peak_allocated,
                peak_cuda_reserved_bytes=peak_reserved,
                process_memory_peak_bytes=None,
                error=None,
            )
        except Exception as exc:
            total = time.perf_counter() - start
            peak_allocated, peak_reserved = cuda_peak_memory()
            return BenchmarkRun(
                input_tokens=self._count_tokens(runner, prompt),
                output_tokens=0,
                load_time_seconds=load_time,
                tokenizer_load_time_seconds=None,
                ttft_seconds=None,
                generation_seconds=total,
                tokens_per_second=None,
                peak_cuda_allocated_bytes=peak_allocated,
                peak_cuda_reserved_bytes=peak_reserved,
                process_memory_peak_bytes=None,
                error=str(exc),
            )

    def _count_tokens(self, runner, text: str) -> int:
        tokenizer = getattr(runner, "tokenizer", None)
        if tokenizer is not None:
            try:
                encoded = tokenizer(text, add_special_tokens=False)
                ids = encoded.get("input_ids", encoded) if isinstance(encoded, dict) else encoded
                return max(1, len(ids))
            except Exception:
                pass
        return max(1, len(text))

    def _fit_prompt(self, runner, prompt: str, context_length: int) -> str:
        if context_length <= 0:
            return prompt
        filler = "\n背景信息：低显存设备需要控制上下文长度、量化方式和并发请求。"
        text = prompt
        while self._count_tokens(runner, text) < context_length:
            text += filler
        tokenizer = getattr(runner, "tokenizer", None)
        if tokenizer is not None:
            try:
                encoded = tokenizer(text, add_special_tokens=False)
                ids = encoded.get("input_ids", encoded) if isinstance(encoded, dict) else encoded
                if len(ids) > context_length and hasattr(tokenizer, "decode"):
                    return tokenizer.decode(ids[-context_length:], skip_special_tokens=True)
            except Exception:
                pass
        return text

    def _apply_adapter(self, runner, adapter_id: str) -> None:
        if hasattr(runner, "load_adapter_by_id"):
            runner.load_adapter_by_id(adapter_id)
            return
        raise RuntimeError("adapter_id was provided but this benchmark runner cannot apply adapters yet.")

    def _seed_everything(self, seed: int) -> None:
        random.seed(seed)
        try:
            import numpy as np

            np.random.seed(seed)
        except Exception:
            pass
        try:
            import torch

            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except Exception:
            pass
