"""Markdown benchmark reports."""

from __future__ import annotations

from .entities import BenchmarkResult, summarize_runs


def render_markdown_report(result: BenchmarkResult) -> str:
    summary = summarize_runs(result.runs)
    lines = [
        f"# LLM-Studio Benchmark {result.id}",
        "",
        "本结果用于本机开发参考；受驱动版本、后台进程、温度、功耗墙、上下文长度和采样参数影响。",
        "",
        "## Config",
        f"- Model: {result.config.model_id}",
        f"- Adapter: {result.config.adapter_id or 'none'}",
        f"- Prompt set: {result.config.prompt_set}",
        f"- Max new tokens: {result.config.max_new_tokens}",
        f"- Context lengths: {', '.join(str(item) for item in result.config.context_lengths)}",
        "",
        "## Environment",
    ]
    for key, value in result.environment.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Summary",
            f"- TTFT avg: {summary['ttft_avg']}",
            f"- Token/s avg: {summary['tokens_per_second_avg']}",
            f"- Token/s median: {summary['tokens_per_second_median']}",
            "",
            "## Runs",
            "| input | output | ttft | generation | token/s | peak allocated | peak reserved | error |",
            "|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for run in result.runs:
        lines.append(
            f"| {run.input_tokens} | {run.output_tokens} | {run.ttft_seconds} | "
            f"{run.generation_seconds:.4f} | {run.tokens_per_second} | "
            f"{run.peak_cuda_allocated_bytes} | {run.peak_cuda_reserved_bytes} | {run.error or ''} |"
        )
    return "\n".join(lines) + "\n"
