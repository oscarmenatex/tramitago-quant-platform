from dataclasses import FrozenInstanceError

import pytest

from quant_platform.strategy_evaluation.domain import (
    EvaluationCriteria,
    InvalidStrategyError,
    Strategy,
)


def make_strategy(**changes: object) -> Strategy:
    values: dict[str, object] = {
        "strategy_id": "strategy-momentum-v1",
        "definition": {"rules": {"signal": "momentum"}, "parameters": {"lookback": 20}},
        "criteria": EvaluationCriteria({"style": "momentum"}),
    }
    values.update(changes)
    return Strategy(**values)  # type: ignore[arg-type]


def test_strategy_preserves_identity_and_immutable_definition() -> None:
    strategy = make_strategy()

    assert strategy.id == "strategy-momentum-v1"
    assert strategy.definition["parameters"]["lookback"] == 20

    with pytest.raises(FrozenInstanceError):
        strategy.strategy_id = "other"
    with pytest.raises(TypeError):
        strategy.definition["parameters"]["lookback"] = 10


@pytest.mark.parametrize(
    "changes",
    [
        {"strategy_id": ""},
        {"definition": {}},
        {"definition": {"": "invalid"}},
        {"criteria": {"style": "momentum"}},
    ],
)
def test_strategy_rejects_invalid_definition(changes: dict[str, object]) -> None:
    with pytest.raises(InvalidStrategyError):
        make_strategy(**changes)
