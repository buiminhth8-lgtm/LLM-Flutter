"""Smoke-check Novel Studio Stage 7 DatasetVersion and Recipe APIs."""

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

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
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
    dataset_id: str | None = None
    revision_ids: list[str] = []
    sample_ids: list[str] = []
    try:
        capabilities = client.request("GET", "/v1/capabilities")
        for name in ("dataset_builder", "dataset_versioning", "dataset_freeze", "training_recipe_recommender"):
            if _capability(capabilities, name) != "available":
                raise RuntimeError(f"{name} capability is not available.")
        if _capability(capabilities, "finetune_runs") != "not_implemented":
            raise RuntimeError("finetune_runs must remain not_implemented.")

        suffix = int(time.time())
        project = client.request(
            "POST",
            "/v1/novels/projects",
            {
                "title": "__stage7_dataset_version_smoke__",
                "slug": f"stage7-dataset-version-smoke-{suffix}",
                "description": "Temporary Stage 7 smoke project.",
            },
        )
        project_id = project["id"]
        chapter = client.request(
            "POST",
            f"/v1/novels/projects/{_quote(project_id)}/chapters",
            {"title": "Smoke Chapter", "outline": "冻结数据集版本。"},
        )
        dataset = client.request(
            "POST",
            "/v1/datasets",
            {"name": "Stage 7 Smoke Dataset", "type": "sft", "project_id": project_id},
        )
        dataset_id = dataset["dataset_id"]
        for index in range(3):
            revision = client.request(
                "POST",
                "/v1/revisions/manual",
                {
                    "project_id": project_id,
                    "chapter_id": chapter["id"],
                    "original_text": f"原始模型文本 {index}",
                    "edited_text": f"人工修订文本 {index}，细节更完整。",
                    "user_score": 5,
                    "accepted_for_dataset": True,
                },
            )
            revision_id = revision["revision_id"]
            revision_ids.append(revision_id)
            client.request("POST", f"/v1/revisions/{_quote(revision_id)}/approve", {})
            sample = client.request(
                "POST",
                f"/v1/datasets/{_quote(dataset_id)}/samples/from-revision",
                {"revision_id": revision_id, "sample_type": "sft"},
            )
            sample_id = sample["sample_id"]
            sample_ids.append(sample_id)
            client.request("POST", f"/v1/datasets/samples/{_quote(sample_id)}/approve", {})

        client.request("POST", f"/v1/datasets/{_quote(dataset_id)}/mark-ready", {})
        version = client.request(
            "POST",
            f"/v1/datasets/{_quote(dataset_id)}/freeze",
            {
                "name": "Stage 7 Smoke v1",
                "split": {"strategy": "group_by_chapter", "val_ratio": 0.1, "seed": 42},
                "dedupe": {"exact_hash": True, "near_duplicate": True},
                "export_format": "sft_jsonl",
            },
        )
        version_id = version["dataset_version_id"]
        manifest = client.request("GET", f"/v1/datasets/versions/{_quote(version_id)}/manifest")
        if manifest.get("dataset_version_id") != version_id:
            raise RuntimeError("Manifest does not reference the created DatasetVersion.")
        version_samples = client.request("GET", f"/v1/datasets/versions/{_quote(version_id)}/samples")
        if not version_samples.get("data"):
            raise RuntimeError("DatasetVersion samples were not created.")
        recipe = client.request(
            "POST",
            f"/v1/datasets/versions/{_quote(version_id)}/recommend-recipe",
            {
                "base_model_id": "qwen-local",
                "method": "qlora",
                "hardware": {"gpu_vram_gb": 8, "cuda_available": True},
                "preferences": {"quality": "balanced", "max_seq_length": 4096},
            },
        )
        recipe = client.request(
            "PATCH",
            f"/v1/datasets/recipes/{_quote(recipe['recipe_id'])}",
            {"user_config": {"epochs": 2}},
        )
        confirmed = client.request("POST", f"/v1/datasets/recipes/{_quote(recipe['recipe_id'])}/confirm", {})
        if confirmed.get("status") != "confirmed" or recipe.get("status") != "draft":
            raise RuntimeError("Recipe confirm flow failed.")
        print(f"Stage 7 smoke passed: dataset_id={dataset_id} version_id={version_id} recipe_id={confirmed['recipe_id']}")
    finally:
        for sample_id in sample_ids:
            try:
                client.request("DELETE", f"/v1/datasets/samples/{_quote(sample_id)}")
            except Exception as exc:
                print(f"Warning: sample archive failed: {exc}")
        if dataset_id:
            try:
                client.request("DELETE", f"/v1/datasets/{_quote(dataset_id)}")
            except Exception as exc:
                print(f"Warning: dataset archive failed: {exc}")
        for revision_id in revision_ids:
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
