from __future__ import annotations

from llm_studio.datasets.recipe_recommender import TrainingRecipeRecommender


def test_recipe_recommender_prefers_qlora_on_8gb_and_warns_small_dataset():
    version = {
        "dataset_version_id": "dsv-1",
        "train_sample_count": 8,
        "val_sample_count": 0,
        "train_token_estimate": 12000,
        "val_token_estimate": 0,
    }
    recipe = TrainingRecipeRecommender().recommend(
        version,
        method="lora",
        hardware={"gpu_vram_gb": 8, "cuda_available": True},
        preferences={"quality": "balanced", "max_seq_length": 4096},
    )
    assert recipe["method"] == "qlora"
    assert recipe["recommended_config"]["batch_size"] == 1
    assert recipe["estimated_vram_gb"] <= 8
    assert {warning["code"] for warning in recipe["warnings"]} >= {
        "DATASET_TOO_SMALL_FOR_TRAINING",
        "DATASET_NO_VALIDATION_SPLIT",
    }
