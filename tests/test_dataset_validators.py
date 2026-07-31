from __future__ import annotations

import pytest

from llm_studio.datasets.entities import TrainingSampleDraft
from llm_studio.datasets.errors import (
    DatasetRevisionNotAcceptedError,
    DatasetSampleEmptyOutputError,
    DatasetSampleUnchangedError,
)
from llm_studio.datasets.validators import (
    validate_revision_for_dataset,
    validate_sample_draft,
)


def test_revision_must_be_dataset_candidate():
    with pytest.raises(DatasetRevisionNotAcceptedError):
        validate_revision_for_dataset(
            {"accepted_for_dataset": False, "status": "approved"}
        )


def test_unapproved_revision_is_warning():
    warnings = validate_revision_for_dataset(
        {"accepted_for_dataset": True, "status": "draft"}
    )
    assert warnings[0]["code"] == "DATASET_REVISION_NOT_APPROVED"


def test_sft_output_validation_and_unchanged_warning():
    with pytest.raises(DatasetSampleEmptyOutputError):
        validate_sample_draft(
            TrainingSampleDraft(
                sample_type="sft",
                instruction="inst",
                input="input",
                output=" ",
                source_hash="s",
                content_hash="c",
            )
        )

    with pytest.raises(DatasetSampleUnchangedError):
        validate_sample_draft(
            TrainingSampleDraft(
                sample_type="sft",
                instruction="inst",
                input="same",
                output="same",
                source_hash="s",
                content_hash="c",
            )
        )

    warnings = validate_sample_draft(
        TrainingSampleDraft(
            sample_type="sft",
            instruction="inst",
            input="input",
            output="original",
            source_hash="s",
            content_hash="c",
        ),
        revision={"original_text": "original"},
    )
    assert warnings[0]["code"] == "DATASET_SAMPLE_UNCHANGED_FROM_ORIGINAL"
