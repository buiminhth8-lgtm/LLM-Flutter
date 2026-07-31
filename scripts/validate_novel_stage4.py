"""Smoke-check Novel Studio Stage 4 against a running local backend."""

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
    try:
        capabilities = client.request("GET", "/v1/capabilities")
        if _capability(capabilities, "writing_workspace") != "available":
            raise RuntimeError("writing_workspace capability is not available.")

        suffix = int(time.time())
        project = client.request(
            "POST",
            "/v1/novels/projects",
            {
                "title": "__stage4_writing_smoke__",
                "slug": f"stage4-writing-smoke-{suffix}",
                "description": "Temporary Stage 4 smoke project.",
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
        template = client.request(
            "POST",
            "/v1/prompts/templates",
            {
                "name": f"Stage 4 Smoke {suffix}",
                "type": "chapter_continue",
                "scope": "global",
                "instruction_template": (
                    "{{project_title}}\n{{chapter_outline}}\n"
                    "{{chapter_draft}}\n{{current_chapter_goal}}\n{{target_length}}"
                ),
                "variables_schema": {},
                "default_values": {},
            },
        )
        template_id = template["id"]
        preview = client.request(
            "POST",
            "/v1/context/render-preview",
            {
                "project_id": project_id,
                "chapter_id": chapter["id"],
                "template_id": template_id,
                "mode": "chapter_continue",
                "target_budget": {
                    "max_tokens": 4096,
                    "reserved_output_tokens": 512,
                    "max_context_tokens": 3000,
                    "max_chars": 12000,
                    "hard_limit": True,
                },
                "user_variables": {
                    "current_chapter_goal": "继续描写主角进入旧城。",
                    "target_length": "200-400 中文字符",
                },
            },
        )
        if not preview.get("rendered_prompt"):
            raise RuntimeError("Context render preview returned an empty prompt.")

        skip_generation = args.skip_generation or not args.model_id
        if skip_generation:
            print("Stage 4 context smoke passed; generation skipped.")
            return

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
                    "max": 400,
                    "strategy": "soft",
                },
                "user_variables": {
                    "current_chapter_goal": "继续描写主角进入旧城。",
                },
                "generation_params": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 512,
                    "repetition_penalty": 1.1,
                },
            },
        )
        generation_id = generation["generation_id"]
        record = client.request(
            "GET",
            f"/v1/writing/generations/{urllib.parse.quote(generation_id)}",
        )
        if record.get("status") != "succeeded" or not record.get("output_hash"):
            raise RuntimeError("Generation record did not complete successfully.")
        client.request(
            "POST",
            f"/v1/writing/generations/{urllib.parse.quote(generation_id)}/save-to-chapter",
            {"target": "draft_content", "append": False},
        )
        saved = client.request(
            "GET",
            f"/v1/novels/chapters/{urllib.parse.quote(chapter['id'])}",
        )
        if saved.get("draft_content") != generation.get("text"):
            raise RuntimeError("Saved chapter draft does not match generation output.")
        print(f"Stage 4 smoke passed: generation_id={generation_id}")
    finally:
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
    parser.add_argument("--model-id", default="")
    parser.add_argument("--skip-generation", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
