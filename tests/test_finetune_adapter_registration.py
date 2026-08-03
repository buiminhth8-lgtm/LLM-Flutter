from __future__ import annotations

from tests.finetune_stage8_utils import fake_finetune_service


def test_adapter_registration_copies_adapter_and_does_not_auto_activate(tmp_path):
    service, _, _, version, recipe, adapter_repo = fake_finetune_service(tmp_path)
    run = service.create_run(
        {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "same-display-name",
            "start_immediately": False,
        }
    )
    layout = service.checkpoints.ensure_run_layout(run["run_id"])
    adapter_dir = layout["adapter"]
    (adapter_dir / "adapter_config.json").write_text(
        '{"peft_type":"LORA","task_type":"CAUSAL_LM","r":16,"lora_alpha":32}',
        encoding="utf-8",
    )
    (adapter_dir / "adapter_model.safetensors").write_bytes(b"adapter")

    result = service.adapter_registration.register(
        run=run,
        adapter_path=adapter_dir,
        metrics={"train_loss": 1.0},
    )

    assert result["adapter_id"] == "adapter-1"
    assert result["auto_activated"] is False
    assert adapter_repo.registered[0].name != "same-display-name"
    assert adapter_repo.registered[0].name.startswith("novel-same-display-name-")
