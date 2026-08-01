import pytest

from quant_platform.strategy_evaluation import (
    ComparisonResult,
    StrategyEvaluationComparison,
)
from quant_platform.strategy_evaluation.domain import (
    StrategyEvaluationComparisonNotFoundError,
)
from quant_platform.strategy_evaluation.registry import (
    StrategyEvaluationComparisonAccess,
    StrategyEvaluationComparisonRegistry,
)


def comparison(identity: str) -> StrategyEvaluationComparison:
    return StrategyEvaluationComparison(
        identity,
        "baseline",
        (f"candidate-{identity}",),
        "stub",
        "1",
        ComparisonResult({"evidence": identity}),
    )


def test_access_delegates_read_operations_and_preserves_instances_and_order():
    registry = StrategyEvaluationComparisonRegistry()
    first, second = (
        registry.register(comparison("first")),
        registry.register(comparison("second")),
    )
    access = StrategyEvaluationComparisonAccess(registry)
    assert access.get("first") is first
    assert access.exists("first") is True and access.exists("missing") is False
    assert access.list() == (first, second)
    assert not hasattr(access, "register")


def test_access_propagates_specific_not_found_error():
    with pytest.raises(StrategyEvaluationComparisonNotFoundError):
        StrategyEvaluationComparisonAccess(StrategyEvaluationComparisonRegistry()).get(
            "missing"
        )
