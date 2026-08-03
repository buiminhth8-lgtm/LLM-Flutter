from __future__ import annotations

import pytest

from llm_studio.finetune.errors import (
    FineTuneBaseModelNotFoundError,
    FineTuneDatasetVersionNotFoundError,
    FineTuneDatasetVersionNotFrozenError,
    FineTuneRecipeDatasetMismatchError,
    FineTuneRecipeNotConfirmedError,
)
from tests.finetune_stage8_utils import fake_finetune_service


def test_preflight_success_with_fake_trainer(tmp_path):
    service, _, _, version, recipe, _ = fake_finetune_service(tmp_path)
    result = service.preflight_public(
        {
            "dataset_version_id": version["dataset_version_id"],
            "recipe_id": recipe["recipe_id"],
            "base_model_id": "qwen-local",
            "adapter_name": "玄幻风格-v1",
        }
    )
    assert result["ok"] is True
    assert result["errors"] == []
    assert result["resolved_config"]["method"] == "qlora"
    assert "model_path" not in result["resolved_config"]


def test_preflight_missing_dataset_version(tmp_path):
    service, _, _, _, recipe, _ = fake_finetune_service(tmp_path)
    with pytest.raises(FineTuneDatasetVersionNotFoundError):
        service.preflight_public(
            {
                "dataset_version_id": "missing",
                "recipe_id": recipe["recipe_id"],
                "base_model_id": "qwen-local",
                "adapter_name": "a",
            }
        )


def test_preflight_requires_frozen_version_and_confirmed_recipe(tmp_path):
    service, datasets, dataset, version, recipe, _ = fake_finetune_service(tmp_path)
    draft = datasets.records.create_dataset_version(
        {
            **version,
            "id": "draft-version",
            "dataset_id": dataset["dataset_id"],
            "version": 99,
            "name": "draft",
            "status": "archived",
        }
    )
    with pytest.raises(FineTuneDatasetVersionNotFrozenError):
        service.preflight_public(
            {
                "dataset_version_id": draft["dataset_version_id"],
                "recipe_id": recipe["recipe_id"],
                "base_model_id": "qwen-local",
                "adapter_name": "a",
            }
        )
    unconfirmed = datasets.records.create_training_recipe(
        {
            "dataset_version_id": version["dataset_version_id"],
            "base_model_id": "qwen-local",
            "method": "qlora",
            "recommended_config": {},
            "status": "draft",
        }
    )
    with pytest.raises(FineTuneRecipeNotConfirmedError):
        service.preflight_public(
            {
                "dataset_version_id": version["dataset_version_id"],
                "recipe_id": unconfirmed["recipe_id"],
                "base_model_id": "qwen-local",
                "adapter_name": "a",
            }
        )


def test_preflight_recipe_mismatch_and_model_missing(tmp_path):
    service, datasets, dataset, version, recipe, _ = fake_finetune_service(tmp_path)
    other = datasets.records.create_dataset_version(
        {
            **version,
            "id": "other-version",
            "dataset_id": dataset["dataset_id"],
            "version": 100,
            "name": "other",
        }
    )
    with pytest.raises(FineTuneRecipeDatasetMismatchError):
        service.preflight_public(
            {
                "dataset_version_id": other["dataset_version_id"],
                "recipe_id": recipe["recipe_id"],
                "base_model_id": "qwen-local",
                "adapter_name": "a",
            }
        )
    with pytest.raises(FineTuneBaseModelNotFoundError):
        service.preflight_public(
            {
                "dataset_version_id": version["dataset_version_id"],
                "recipe_id": recipe["recipe_id"],
                "base_model_id": "missing-model",
                "adapter_name": "a",
            }
        )
