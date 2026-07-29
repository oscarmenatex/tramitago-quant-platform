from dataclasses import FrozenInstanceError

import pytest

from quant_platform.strategy_evaluation.domain import (
    EvaluationCriteria,
    InvalidEvaluationCriteriaError,
)


def test_criteria_is_an_immutable_value_object() -> None:
    criteria = EvaluationCriteria({"style": "momentum", "thresholds": [0.2]})

    assert criteria == EvaluationCriteria({"style": "momentum", "thresholds": [0.2]})
    assert criteria.criteria["thresholds"] == (0.2,)

    with pytest.raises(FrozenInstanceError):
        criteria.values = {}
    with pytest.raises(TypeError):
        criteria.criteria["style"] = "value"


@pytest.mark.parametrize("values", [{}, {"": "momentum"}, []])
def test_criteria_rejects_invalid_values(values: object) -> None:
    with pytest.raises(InvalidEvaluationCriteriaError):
        EvaluationCriteria(values)  # type: ignore[arg-type]
