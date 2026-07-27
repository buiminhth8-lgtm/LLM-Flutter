"""Markdown benchmark reports."""

from __future__ import annotations

from .entities import BenchmarkResult, summarize_runs


def render_markdown_report(result: BenchmarkResult) -> str:
    summary = summarize_runs(result.runs)
    lines = [
        f"# LLM-Studio Benchmark {result.id}",
        "",
        "估算和基准结果仅代表本次运行，不代表稳定长期性能。",
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
            "| input | output | ttft | generation | token/s | peak allocated | error |",
            "|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for run in result.runs:
        lines.append(
            f"| {run.input_tokens} | {run.output_tokens} | {run.ttft_seconds} | "
            f"{run.generation_seconds:.4f} | {run.tokens_per_second} | "
            f"{run.peak_cuda_allocated_bytes} | {run.error or ''} |"
        )
    return "\n".join(lines) + "\n"
