"""Smoke helper for Novel Studio Stage 11 Evaluation Center.

This script is intentionally conservative. It assumes a running local backend,
creates disposable novel records, runs heuristic evaluation on a chapter, adds a
manual score, generates a report, and cleans up the temporary project. It does
not call a cloud judge, create training samples, freeze datasets, export JSONL,
start fine-tuning, activate adapters, or package Windows artifacts.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


def _request(
    base_url: str,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode("utf-8")
        raise SystemExit(f"{method} {path} failed: {exc.code} {payload}") from exc


def _try_cleanup(base_url: str, project_id: str | None) -> None:
    if not project_id:
        return
    try:
        _request(base_url, "DELETE", f"/v1/novels/projects/{project_id}")
    except SystemExit as exc:
        print(f"cleanup warning: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base_url = args.base_url
    project_id: str | None = None

    try:
        caps = _request(base_url, "GET", "/v1/capabilities")
        by_name = {item["name"]: item for item in caps.get("capabilities", [])}
        assert by_name["full_evaluation_center"]["status"] == "available"
        assert by_name["evaluation_repetition"]["status"] == "available"
        assert by_name["windows_packaging"]["status"] == "not_implemented"

        project = _request(
            base_url,
            "POST",
            "/v1/novels/projects",
            {
                "title": "__stage11_evaluation_smoke__",
                "genre": "玄幻",
                "target_style": "紧张、克制、细节明确",
            },
        )
        project_id = project["id"]
        chapter = _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/chapters",
            {
                "title": "黑市",
                "draft_content": (
                    "夜色沉入旧城。林烬进入黑市，发现灵骨交易与父亲死因有关。"
                    "夜色沉入旧城。她没有立刻后退，而是记下卖家的骨纹印记。"
                ),
                "summary": "林烬在黑市发现灵骨交易线索。",
            },
        )
        chapter_id = chapter["id"]
        _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/characters",
            {"name": "林烬", "background": "追查父亲死因。"},
        )
        _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/world-entries",
            {
                "category": "地点",
                "title": "黑市",
                "content": "黑市位于旧城地下，禁止普通守卫进入。",
                "priority": 10,
            },
        )
        run = _request(
            base_url,
            "POST",
            "/v1/evaluation/runs",
            {
                "name": "Stage 11 smoke evaluation",
                "target_type": "chapter",
                "target_id": chapter_id,
                "evaluator_config": {
                    "enabled_evaluators": [
                        "repetition",
                        "style_consistency",
                        "character_consistency",
                        "world_consistency",
                        "plot_coherence",
                        "pacing",
                        "memory_usage",
                        "foreshadowing",
                    ]
                },
            },
        )
        assert run["status"] == "completed"
        run_id = run["run_id"]
        metrics = _request(base_url, "GET", f"/v1/evaluation/runs/{run_id}/metrics")
        assert metrics["data"]
        findings = _request(base_url, "GET", f"/v1/evaluation/runs/{run_id}/findings")
        if findings["data"]:
            finding_id = findings["data"][0]["finding_id"]
            _request(
                base_url,
                "PATCH",
                f"/v1/evaluation/findings/{finding_id}",
                {"status": "acknowledged"},
            )
        _request(
            base_url,
            "POST",
            f"/v1/evaluation/runs/{run_id}/manual-score",
            {
                "reviewer_id": "stage11-smoke",
                "overall_score": 4,
                "dimensions": {"style": 4, "plot": 4},
                "notes": "Smoke run manual note.",
            },
        )
        report = _request(base_url, "POST", f"/v1/evaluation/runs/{run_id}/report")
        assert report["report_id"]
        reports = _request(base_url, "GET", f"/v1/evaluation/runs/{run_id}/reports")
        assert reports["data"]
        print(
            json.dumps(
                {
                    "project_id": project_id,
                    "chapter_id": chapter_id,
                    "run_id": run_id,
                    "report_id": report["report_id"],
                    "metrics": len(metrics["data"]),
                    "findings": len(findings["data"]),
                },
                ensure_ascii=False,
            )
        )
    finally:
        _try_cleanup(base_url, project_id)


if __name__ == "__main__":
    main()
