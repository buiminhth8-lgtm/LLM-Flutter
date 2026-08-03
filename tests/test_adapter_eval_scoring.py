from __future__ import annotations

import pytest

from llm_studio.adapter_evaluation.errors import (
    AdapterEvalInvalidScoreError,
    AdapterEvalInvalidWinnerError,
)
from llm_studio.adapter_evaluation.scoring import (
    validate_dimensions,
    validate_score,
    validate_winner,
)


def test_adapter_eval_score_and_winner_validation():
    assert validate_score(5, "base_score") == 5
    assert validate_winner("adapter") == "adapter"
    assert validate_dimensions({"style": {"base": 3, "adapter": 4}})["style"]["adapter"] == 4
    with pytest.raises(AdapterEvalInvalidScoreError):
        validate_score(6, "base_score")
    with pytest.raises(AdapterEvalInvalidScoreError):
        validate_dimensions({"unknown": {"base": 3}})
    with pytest.raises(AdapterEvalInvalidWinnerError):
        validate_winner("model")
