"""Smoke helper for Novel Studio Stage 10 Memory / RAG.

The script is intentionally conservative: it does not start training, does not
call external vector databases, and does not require a real model. It assumes a
running local backend and creates disposable test records.
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from typing import Any


def _request(base_url: str, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
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
        with urllib.request.urlopen(request, timeout=20) as response:
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
        assert by_name["novel_rag_memory"]["status"] == "available"
        assert by_name["memory_embedding_retrieval"]["status"] == "not_implemented"

        project = _request(
            base_url,
            "POST",
            "/v1/novels/projects",
            {"title": "__stage10_memory_smoke__"},
        )
        project_id = project["id"]
        chapter = _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/chapters",
            {
                "title": "黑市",
                "draft_content": "主角进入旧城黑市，发现灵骨交易与父亲死因有关。",
                "summary": "主角进入黑市。",
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
            {"category": "地点", "title": "黑市", "content": "黑市位于旧城地下。", "priority": 10},
        )
        _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/plot-threads",
            {"title": "灵骨交易", "description": "灵骨交易与父亲死因相关。"},
        )
        _request(
            base_url,
            "POST",
            f"/v1/novels/projects/{project_id}/timeline-events",
            {"title": "骨片印记", "description": "主角发现黑市印记。"},
        )
        build = _request(
            base_url,
            "POST",
            f"/v1/memory/projects/{project_id}/build-from-novel",
            {"include": {"generations": False, "adapter_eval_results": False}, "rebuild_index": True},
        )
        assert build["documents_created"] >= 1
        _request(base_url, "POST", f"/v1/memory/projects/{project_id}/index/rebuild", {})
        retrieved = _request(
            base_url,
            "POST",
            "/v1/memory/retrieve",
            {
                "project_id": project_id,
                "chapter_id": chapter_id,
                "query_text": "主角进入黑市，发现灵骨交易。",
                "top_k": 8,
                "budget": {"max_memory_tokens": 800, "max_chunks": 5},
            },
        )
        assert retrieved["chunks"]
        summary = _request(
            base_url,
            "POST",
            f"/v1/memory/chapters/{chapter_id}/summaries",
            {"summary_text": "主角进入黑市，发现灵骨交易。", "set_active": True},
        )
        assert summary["status"] == "active"
        print(json.dumps({"project_id": project_id, "retrieval_id": retrieved["retrieval_id"]}, ensure_ascii=False))
    finally:
        _try_cleanup(base_url, project_id)


if __name__ == "__main__":
    main()
