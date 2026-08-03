"""Feature flag helpers."""

from __future__ import annotations

from typing import Any


def is_novel_studio_enabled(config: Any) -> bool:
    """Return whether Novel Studio is enabled.

    The flag is intentionally false by default. Stage 0 only prepares the
    engineering entry point; it must not expose Novel Studio business surfaces.
    """

    try:
        features = config.get("features", {}) if config is not None else {}
        if not isinstance(features, dict):
            return False
        novel = features.get("novel_studio", {})
        if not isinstance(novel, dict):
            return False
        return bool(novel.get("enabled", False))
    except Exception:
        return False


def is_revision_system_enabled(config: Any) -> bool:
    """Return whether the Stage 5 revision API should be exposed."""

    if not is_novel_studio_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        revision = features.get("revision_system", {})
        if not isinstance(revision, dict):
            return True
        return bool(revision.get("enabled", True))
    except Exception:
        return False


def is_dataset_builder_enabled(config: Any) -> bool:
    """Return whether the Stage 6 Dataset Builder API should be exposed."""

    if not is_revision_system_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        dataset = features.get("dataset_builder", {})
        if not isinstance(dataset, dict):
            return True
        return bool(dataset.get("enabled", True))
    except Exception:
        return False


def is_dataset_versioning_enabled(config: Any) -> bool:
    """Return whether Stage 7 DatasetVersion APIs should be exposed."""

    if not is_dataset_builder_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        versioning = features.get("dataset_versioning", {})
        if not isinstance(versioning, dict):
            return True
        return bool(versioning.get("enabled", True))
    except Exception:
        return False


def is_training_recipe_recommender_enabled(config: Any) -> bool:
    """Return whether Stage 7 training recipe recommendation APIs should be exposed."""

    if not is_dataset_versioning_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        recipe = features.get("training_recipe_recommender", {})
        if not isinstance(recipe, dict):
            return True
        return bool(recipe.get("enabled", True))
    except Exception:
        return False


def is_finetune_center_enabled(config: Any) -> bool:
    """Return whether Stage 8 Fine-tune Center APIs should be exposed."""

    if not is_training_recipe_recommender_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        finetune = features.get("finetune_center", {})
        if not isinstance(finetune, dict):
            return True
        return bool(finetune.get("enabled", True))
    except Exception:
        return False


def is_adapter_evaluation_enabled(config: Any) -> bool:
    """Return whether Stage 9 Adapter Evaluation APIs should be exposed."""

    if not is_finetune_center_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        adapter_eval = features.get("adapter_evaluation", {})
        if not isinstance(adapter_eval, dict):
            return True
        return bool(adapter_eval.get("enabled", True))
    except Exception:
        return False


def is_novel_memory_enabled(config: Any) -> bool:
    """Return whether Stage 10 Novel Memory / RAG APIs should be exposed."""

    if not is_adapter_evaluation_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        memory = features.get("novel_memory", {})
        if not isinstance(memory, dict):
            return True
        return bool(memory.get("enabled", True))
    except Exception:
        return False


def is_memory_retrieval_enabled(config: Any) -> bool:
    """Return whether Stage 10 Memory retrieval should be exposed."""

    if not is_novel_memory_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        retrieval = features.get("memory_retrieval", {})
        if not isinstance(retrieval, dict):
            return True
        return bool(retrieval.get("enabled", True))
    except Exception:
        return False


def is_evaluation_center_enabled(config: Any) -> bool:
    """Return whether Stage 11 Evaluation Center APIs should be exposed."""

    if not is_novel_memory_enabled(config):
        return False
    try:
        features = config.get("features", {}) if config is not None else {}
        if not isinstance(features, dict) or "evaluation_center" not in features:
            return False
        evaluation = features.get("evaluation_center", {})
        if not isinstance(evaluation, dict):
            return False
        return bool(evaluation.get("enabled", True))
    except Exception:
        return False
