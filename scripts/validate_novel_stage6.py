"""Smoke-check Novel Studio Stage 6 Dataset Builder against a running backend."""

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


def _quote(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def run(args: argparse.Namespace) -> None:
    client = ApiClient(args.base_url, user_id=args.user_id, api_key=args.api_key)
    project_id: str | None = None
    revision_id: str | None = None
    dataset_id: str | None = None
    sample_id: str | None = None
    try:
        capabilities = client.request("GET", "/v1/capabilities")
        if _capability(capabilities, "dataset_builder") != "available":
            raise RuntimeError("dataset_builder capability is not available.")
        if _capability(capabilities, "dataset_sft_export") != "available":
            raise RuntimeError("dataset_sft_export capability is not available.")
        if _capability(capabilities, "dataset_versioning") != "not_implemented":
            raise RuntimeError("dataset_versioning must remain not_implemented.")

        suffix = int(time.time())
        project = client.request(
            "POST",
            "/v1/novels/projects",
            {
                "title": "__stage6_dataset_smoke__",
                "slug": f"stage6-dataset-smoke-{suffix}",
                "description": "Temporary Stage 6 smoke project.",
            },
        )
        project_id = project["id"]
        chapter = client.request(
            "POST",
            f"/v1/novels/projects/{_quote(project_id)}/chapters",
            {
                "title": "Smoke Chapter",
                "outline": "主角进入旧城并发现异常。",
                "draft_content": "旧城的雨刚刚停。",
            },
        )

        revision = client.request(
            "POST",
            "/v1/revisions/manual",
            {
                "project_id": project_id,
                "chapter_id": chapter["id"],
                "original_text": "旧城的雨停了。他很紧张。",
                "edited_text": "旧城的雨停了，石阶上浮着冷光，他的指节微微发白。",
                "edit_tags": ["language_polish", "detail_expand"],
                "user_score": 5,
                "accepted_for_dataset": True,
            },
        )
        revision_id = revision["revision_id"]
        approved_revision = client.request(
            "POST",
            f"/v1/revisions/{_quote(revision_id)}/approve",
            {},
        )
        if approved_revision.get("status") != "approved":
            raise RuntimeError("Revision was not approved.")

        dataset = client.request(
            "POST",
            "/v1/datasets",
            {
                "name": "Stage 6 Smoke Dataset",
                "type": "sft",
                "project_id": project_id,
            },
        )
        dataset_id = dataset["dataset_id"]

        sample = client.request(
            "POST",
            f"/v1/datasets/{_quote(dataset_id)}/samples/from-revision",
            {"revision_id": revision_id, "sample_type": "sft"},
        )
        sample_id = sample["sample_id"]
        if sample.get("output") != "旧城的雨停了，石阶上浮着冷光，他的指节微微发白。":
            raise RuntimeError("Sample output does not match edited revision text.")

        approved_sample = client.request(
            "POST",
            f"/v1/datasets/samples/{_quote(sample_id)}/approve",
            {},
        )
        if approved_sample.get("status") != "approved":
            raise RuntimeError("Sample was not approved.")

        export = client.request(
            "POST",
            f"/v1/datasets/{_quote(dataset_id)}/export",
            {"format": "sft_jsonl", "approved_only": True},
        )
        if export.get("sample_count") != 1 or not export.get("export_hash"):
            raise RuntimeError("SFT JSONL export record is invalid.")
        if str(export.get("export_path", "")).startswith(("/", "\\")) or ":\\" in str(export.get("export_path", "")):
            raise RuntimeError("Export path must be relative and safe.")

        print(
            "Stage 6 smoke passed: "
            f"dataset_id={dataset_id} sample_id={sample_id} export_id={export['export_id']}"
        )
    finally:
        if sample_id:
            try:
                client.request("DELETE", f"/v1/datasets/samples/{_quote(sample_id)}")
            except Exception as exc:
                print(f"Warning: sample archive failed: {exc}")
        if dataset_id:
            try:
                client.request("DELETE", f"/v1/datasets/{_quote(dataset_id)}")
            except Exception as exc:
                print(f"Warning: dataset archive failed: {exc}")
        if revision_id:
            try:
                client.request("DELETE", f"/v1/revisions/{_quote(revision_id)}")
            except Exception as exc:
                print(f"Warning: revision archive failed: {exc}")
        if project_id:
            try:
                client.request("DELETE", f"/v1/novels/projects/{_quote(project_id)}")
            except Exception as exc:
                print(f"Warning: project cleanup failed: {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", default="admin")
    parser.add_argument("--api-key", default="")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
