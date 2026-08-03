from __future__ import annotations

from llm_studio.finetune.logs import sanitize_finetune_log
from tests.finetune_stage8_utils import fake_finetune_service


def test_metrics_and_logs_repository_roundtrip(tmp_path):
    service, _, _, version, recipe, _ = fake_finetune_service(tmp_path)
    run = service.create_run(
        {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "a",
            "start_immediately": False,
        }
    )
    service.records.create_metric(
        {
            "run_id": run["run_id"],
            "step": 1,
            "metric_type": "train",
            "metrics": {"train_loss": 2.91, "learning_rate": 0.00018},
        }
    )
    service.records.create_log(
        {"run_id": run["run_id"], "level": "info", "message": "hello", "step": 1}
    )

    assert service.get_metrics(run["run_id"])[0]["metrics"]["train_loss"] == 2.91
    assert service.get_logs(run["run_id"])[0]["message"] == "hello"


def test_logs_are_redacted_and_traceback_hidden():
    message = sanitize_finetune_log(
        "Traceback (most recent call last):\n"
        '  File "secret.py", line 1\n'
        "api_key=super-secret\n"
        "useful message"
    )

    assert "Traceback" not in message
    assert "secret.py" not in message
    assert "super-secret" not in message
    assert "useful message" in message
