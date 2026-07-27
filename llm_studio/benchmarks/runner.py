"""Benchmark runner."""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable

from llm_studio.generation import GenerationConfig
from llm_studio.runtime.capabilities import detect_runtime_capabilities

from .entities import BenchmarkConfig, BenchmarkResult, BenchmarkRun
from .metrics import cuda_peak_memory, sync_cuda, tokens_per_second
from .prompts import get_prompt_set
from .repository import BenchmarkRepository


class BenchmarkRunner:
    def __init__(self, config, runner_factory: Callable[[str], object], repository: BenchmarkRepository | None = None):
        self.config = config
        self.runner_factory = runner_factory
        self.repository = repository or BenchmarkRepository(config)

    def run(self, benchmark_config: BenchmarkConfig) -> BenchmarkResult:
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
        sync_cuda()
        load_time = time.perf_counter() - load_start

        try:
            total_runs = benchmark_config.warmup_runs + benchmark_config.measured_runs
            for idx in range(total_runs):
                context_length = benchmark_config.context_lengths[
                    idx % len(benchmark_config.context_lengths)
                ]
                prompt = self._fit_prompt(prompts[idx % len(prompts)], context_length)
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
            return BenchmarkRun(
                input_tokens=self._count_tokens(runner, prompt),
                output_tokens=0,
                load_time_seconds=load_time,
                tokenizer_load_time_seconds=None,
                ttft_seconds=None,
                generation_seconds=total,
                tokens_per_second=None,
                peak_cuda_allocated_bytes=None,
                peak_cuda_reserved_bytes=None,
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

    def _fit_prompt(self, prompt: str, context_length: int) -> str:
        if context_length <= 0:
            return prompt
        filler = "\n背景信息：低显存设备需要控制上下文长度、量化方式和并发请求。"
        text = prompt
        while len(text) < context_length:
            text += filler
        return text[-context_length:]
