from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from quant_platform.strategy_evaluation.domain import (
    EvaluationContext,
    InvalidEvaluationContextError,
)


def make_context(**changes: object) -> EvaluationContext:
    values: dict[str, object] = {
        "period_start": date(2024, 1, 1),
        "period_end": date(2024, 12, 31),
        "asset_universe": ("AAPL", "MSFT"),
        "temporal_horizon": "one_year",
        "market_regime": "mixed",
        "restrictions": {"long_only": True, "limits": {"max_weight": 0.1}},
    }
    values.update(changes)
    return EvaluationContext(**values)  # type: ignore[arg-type]


def test_context_is_immutable_and_equal_by_value() -> None:
    context = make_context()

    assert context == make_context(asset_universe=["AAPL", "MSFT"])
    assert context.evaluation_period == (date(2024, 1, 1), date(2024, 12, 31))

    with pytest.raises(FrozenInstanceError):
        context.market_regime = "bear"
    with pytest.raises(TypeError):
        context.restrictions["limits"]["max_weight"] = 0.2


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"period_start": date(2025, 1, 1)}, "start"),
        ({"asset_universe": ()}, "universe"),
        ({"temporal_horizon": ""}, "horizon"),
        ({"market_regime": ""}, "regime"),
        ({"restrictions": []}, "Restrictions"),
    ],
)
def test_context_rejects_invalid_values(changes: dict[str, object], message: str) -> None:
    with pytest.raises(InvalidEvaluationContextError, match=message):
        make_context(**changes)
