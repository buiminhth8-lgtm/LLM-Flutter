"""Stage 8 Fine-tune Center smoke validation.

Default mode uses an in-process FastAPI app with the explicit fake trainer. It
does not require GPU, does not load a real model, and does not perform real
training. Pass --real-trainer to verify real preflight behavior instead.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from llm_studio.api.deps import get_api_state
from llm_studio.api_server import get_app
from llm_studio.config import Config

PROJECT_NAME = "__stage8_finetune_smoke__"


def _write_config(root: Path, *, fake_trainer: bool) -> Path:
    cfg_path = root / "config.yaml"
    cfg_path.write_text(
        f"""
auth:
  enabled: false
api:
  allowed_origins: []
features:
  novel_studio:
    enabled: true
  finetune_center:
    enabled: true
models:
  root_dir: ./data/models
  temp_dir: ./data/downloads
  metadata_cache: ./data/model_index.json
  adapters_dir: ./data/adapters
novels:
  db_path: ./data/novels/novels.sqlite
finetune:
  db_path: ./data/novels/novels.sqlite
  output_dir: ./data/finetune
  use_fake_trainer: {str(fake_trainer).lower()}
""",
        encoding="utf-8",
    )
    model_dir = root / "data" / "models" / "transformers" / "qwen-local"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text('{"model_type":"qwen2"}', encoding="utf-8")
    (model_dir / "model.safetensors").write_bytes(b"fake-model")
    index_path = root / "data" / "model_index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "models": [
                    {
                        "id": "qwen-local",
                        "display_name": "qwen-local",
                        "path": str(model_dir),
                        "format": "transformers",
                        "status": "ready",
                        "architecture": "qwen2",
                        "parameter_count": 1_500_000_000,
                        "quantization": None,
                        "context_length": 4096,
                        "size_bytes": 1,
                        "files": ["config.json", "model.safetensors"],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return cfg_path


def _ok(response, label: str):
    if response.status_code >= 400:
        raise RuntimeError(f"{label} failed: {response.status_code} {response.text}")
    return response.json()


def run_smoke(*, real_trainer: bool) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="stage8_finetune_") as tmp:
        root = Path(tmp)
        config = Config(_write_config(root, fake_trainer=not real_trainer))
        client = TestClient(get_app(config))
        caps = _ok(client.get("/v1/capabilities"), "capabilities")["capabilities"]
        cap_map = {item["name"]: item["status"] for item in caps}
        if cap_map.get("finetune_center") != "available":
            raise RuntimeError("finetune_center capability is not available.")

        project = _ok(
            client.post("/v1/novels/projects", json={"title": PROJECT_NAME}),
            "create project",
        )
        volume = _ok(
            client.post(
                f"/v1/novels/projects/{project['id']}/volumes",
                json={"title": "Smoke Volume"},
            ),
            "create volume",
        )
        chapter = _ok(
            client.post(
                f"/v1/novels/projects/{project['id']}/chapters",
                json={"title": "Smoke Chapter", "volume_id": volume["id"]},
            ),
            "create chapter",
        )
        revision = _ok(
            client.post(
                "/v1/revisions/manual",
                json={
                    "project_id": project["id"],
                    "chapter_id": chapter["id"],
                    "original_text": "模型原文",
                    "edited_text": "人工修订正文",
                    "user_score": 4,
                    "accepted_for_dataset": True,
                },
            ),
            "create revision",
        )
        revision = _ok(
            client.post(f"/v1/revisions/{revision['revision_id']}/approve"),
            "approve revision",
        )
        dataset = _ok(
            client.post(
                "/v1/datasets",
                json={"name": PROJECT_NAME, "project_id": project["id"]},
            ),
            "create dataset",
        )
        sample = _ok(
            client.post(
                f"/v1/datasets/{dataset['dataset_id']}/samples/from-revision",
                json={"revision_id": revision["revision_id"]},
            ),
            "create sample",
        )
        _ok(client.post(f"/v1/datasets/samples/{sample['sample_id']}/approve"), "approve sample")
        _ok(client.post(f"/v1/datasets/{dataset['dataset_id']}/mark-ready"), "mark ready")
        version = _ok(
            client.post(f"/v1/datasets/{dataset['dataset_id']}/freeze", json={"name": "smoke-v1"}),
            "freeze",
        )
        recipe = _ok(
            client.post(
                f"/v1/datasets/versions/{version['dataset_version_id']}/recommend-recipe",
                json={"base_model_id": "qwen-local", "hardware": {"gpu_vram_gb": 8}},
            ),
            "recommend recipe",
        )
        recipe = _ok(
            client.post(f"/v1/datasets/recipes/{recipe['recipe_id']}/confirm"),
            "confirm recipe",
        )
        request = {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "stage8-smoke-adapter",
        }
        preflight = _ok(client.post("/v1/finetune/preflight", json=request), "preflight")
        if not preflight["ok"]:
            if real_trainer:
                return {"preflight": preflight, "real_trainer": True}
            raise RuntimeError(f"fake preflight failed: {preflight}")
        run = _ok(
            client.post("/v1/finetune/runs", json={**request, "start_immediately": True}),
            "create finetune run",
        )
        get_api_state().job_queue.shutdown(wait=True)
        detail = _ok(client.get(f"/v1/finetune/runs/{run['run_id']}"), "get run")
        metrics = _ok(client.get(f"/v1/finetune/runs/{run['run_id']}/metrics"), "metrics")
        checkpoints = _ok(
            client.get(f"/v1/finetune/runs/{run['run_id']}/checkpoints"),
            "checkpoints",
        )
        if detail["status"] != "completed":
            raise RuntimeError(f"run did not complete: {detail}")
        if not detail.get("adapter_id"):
            raise RuntimeError("adapter was not registered.")
        return {
            "run_id": run["run_id"],
            "status": detail["status"],
            "adapter_id": detail["adapter_id"],
            "metric_count": len(metrics["data"]),
            "checkpoint_count": len(checkpoints["data"]),
            "fake_trainer": not real_trainer,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--real-trainer", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run_smoke(real_trainer=args.real_trainer), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
