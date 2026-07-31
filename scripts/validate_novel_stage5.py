"""Smoke-check Novel Studio Stage 5 revisions against a running backend."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class ApiClient:
    def __init__(self, base_url: str, *, user_id: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers.update(
                {
                    "Authorization": f"Bearer {api_key}",
                    "X-API-Key": api_key,
                    "X-User-ID": user_id,
                }
            )

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=payload,
            headers=self.headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"{method} {path} failed: HTTP {exc.code} {detail}") from exc
        return json.loads(raw) if raw else {}


def _capability(payload: dict[str, Any], name: str) -> str:
    for item in payload.get("capabilities", []):
        if item.get("name") == name:
            return str(item.get("status") or "")
    return ""


def run(args: argparse.Namespace) -> None:
    client = ApiClient(args.base_url, user_id=args.user_id, api_key=args.api_key)
    project_id: str | None = None
    template_id: str | None = None
    revision_id: str | None = None
    try:
        capabilities = client.request("GET", "/v1/capabilities")
        if _capability(capabilities, "revision_system") != "available":
            raise RuntimeError("revision_system capability is not available.")
        if _capability(capabilities, "dataset_versioning") not in {"", "not_implemented"}:
            raise RuntimeError("dataset_versioning must remain not_implemented.")

        suffix = int(time.time())
        project = client.request(
            "POST",
            "/v1/novels/projects",
            {
                "title": "__stage5_revision_smoke__",
                "slug": f"stage5-revision-smoke-{suffix}",
                "description": "Temporary Stage 5 smoke project.",
            },
        )
        project_id = project["id"]
        chapter = client.request(
            "POST",
            f"/v1/novels/projects/{project_id}/chapters",
            {
                "title": "Smoke Chapter",
                "outline": "主角进入旧城并发现异常。",
                "draft_content": "旧城的雨刚刚停。",
            },
        )

        generation_id = args.generation_id
        if not generation_id and args.model_id:
            template = client.request(
                "POST",
                "/v1/prompts/templates",
                {
                    "name": f"Stage 5 Smoke {suffix}",
                    "type": "chapter_continue",
                    "scope": "global",
                    "instruction_template": "{{project_title}}\n{{chapter_outline}}\n{{chapter_draft}}",
                    "variables_schema": {},
                    "default_values": {},
                },
            )
            template_id = template["id"]
            generation = client.request(
                "POST",
                "/v1/writing/generate",
                {
                    "project_id": project_id,
                    "chapter_id": chapter["id"],
                    "template_id": template_id,
                    "model_id": args.model_id,
                    "mode": "chapter_continue",
                    "target_length": {
                        "unit": "chars",
                        "min": 1,
                        "max": 300,
                        "strategy": "soft",
                    },
                    "generation_params": {"max_tokens": 256},
                },
            )
            generation_id = generation["generation_id"]

        if not generation_id:
            print("Stage 5 capabilities and project smoke passed; from-generation skipped.")
            print("Pass --generation-id or --model-id to exercise revision creation.")
            return

        revision = client.request(
            "POST",
            "/v1/revisions/from-generation",
            {
                "generation_id": generation_id,
                "edited_text": "旧城的雨停了，石阶上还浮着冷光。",
                "edit_tags": ["language_polish", "detail_expand"],
                "user_score": 4,
                "quality_notes": "Smoke revision.",
                "accepted_for_dataset": True,
            },
        )
        revision_id = revision["revision_id"]
        if revision.get("source") != "generation":
            raise RuntimeError("Revision source is not generation.")
        if not revision.get("diff", {}).get("ops"):
            raise RuntimeError("Revision diff_json is empty.")

        updated = client.request(
            "PATCH",
            f"/v1/revisions/{urllib.parse.quote(revision_id)}",
            {
                "edited_text": "旧城的雨停了，石阶上浮着冷光，像有什么正在醒来。",
                "edit_tags": ["language_polish", "detail_expand", "scene_atmosphere"],
                "user_score": 5,
                "accepted_for_dataset": True,
                "expected_updated_at": revision["updated_at"],
            },
        )
        if updated.get("user_score") != 5:
            raise RuntimeError("Revision update did not persist score.")

        approved = client.request(
            "POST",
            f"/v1/revisions/{urllib.parse.quote(revision_id)}/approve",
            {},
        )
        if approved.get("status") != "approved":
            raise RuntimeError("Revision approve did not set approved status.")

        listed = client.request(
            "GET",
            f"/v1/revisions?generation_id={urllib.parse.quote(generation_id)}",
        )
        if not listed.get("data"):
            raise RuntimeError("Revision list did not return the created record.")
        print(f"Stage 5 smoke passed: revision_id={revision_id}")
    finally:
        if revision_id:
            try:
                client.request(
                    "DELETE",
                    f"/v1/revisions/{urllib.parse.quote(revision_id)}",
                )
            except Exception as exc:
                print(f"Warning: revision archive failed: {exc}")
        if template_id:
            try:
                client.request(
                    "DELETE",
                    f"/v1/prompts/templates/{urllib.parse.quote(template_id)}",
                )
            except Exception as exc:
                print(f"Warning: template cleanup failed: {exc}")
        if project_id:
            try:
                client.request(
                    "DELETE",
                    f"/v1/novels/projects/{urllib.parse.quote(project_id)}",
                )
            except Exception as exc:
                print(f"Warning: project cleanup failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="admin")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--generation-id", default="")
    parser.add_argument("--model-id", default="")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
