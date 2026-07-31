import pytest

from llm_studio.revisions.errors import RevisionInvalidScoreError
from llm_studio.revisions.scoring import dataset_candidate_warnings, validate_user_score


def test_revision_score_validation_allows_empty_and_one_to_five():
    assert validate_user_score(None) is None
    assert validate_user_score(1) == 1
    assert validate_user_score("5") == 5


def test_revision_score_validation_rejects_out_of_range():
    with pytest.raises(RevisionInvalidScoreError):
        validate_user_score(0)
    with pytest.raises(RevisionInvalidScoreError):
        validate_user_score(6)


def test_low_score_dataset_candidate_returns_warning():
    warnings = dataset_candidate_warnings(accepted_for_dataset=True, user_score=3)
    assert warnings[0]["code"] == "REVISION_LOW_SCORE_DATASET_CANDIDATE"
    assert dataset_candidate_warnings(accepted_for_dataset=True, user_score=4) == []
