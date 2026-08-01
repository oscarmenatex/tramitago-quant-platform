import pytest

from quant_platform.strategy_evaluation import (
    ComparisonResult,
    StrategyEvaluationComparison,
    StrategyEvaluationComparisonAccess,
    StrategyEvaluationComparisonRegistry,
)
from quant_platform.strategy_evaluation.domain import (
    DuplicateStrategyEvaluationComparisonError,
    StrategyEvaluationComparisonNotFoundError,
)


def make_comparison(comparison_id: str = "comparison-001") -> StrategyEvaluationComparison:
    return StrategyEvaluationComparison(
        comparison_id, "baseline", ("candidate",), "stub", "1.0", ComparisonResult({"x": 1})
    )


def test_registry_and_access_are_read_only_and_preserve_instances() -> None:
    registry = StrategyEvaluationComparisonRegistry()
    comparison = registry.register(make_comparison())
    access = StrategyEvaluationComparisonAccess(registry)
    assert access.get(comparison.id) is comparison
    assert access.list() == (comparison,)
    assert not hasattr(access, "register")
    with pytest.raises(DuplicateStrategyEvaluationComparisonError):
        registry.register(make_comparison())
    with pytest.raises(StrategyEvaluationComparisonNotFoundError):
        access.get("missing")
