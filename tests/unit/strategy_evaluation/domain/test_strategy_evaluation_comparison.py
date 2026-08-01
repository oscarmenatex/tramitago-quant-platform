import pytest

from quant_platform.strategy_evaluation.domain import (
    ComparisonResult,
    InvalidStrategyEvaluationComparisonError,
    StrategyEvaluationComparison,
)


def make_comparison(**changes: object) -> StrategyEvaluationComparison:
    values: dict[str, object] = {
        "comparison_id": "comparison-001",
        "baseline_evaluation_id": "baseline",
        "candidate_evaluation_ids": ("candidate-1", "candidate-2"),
        "comparison_method_id": "stub",
        "comparison_method_version": "1.0",
        "result": ComparisonResult({"evidence": True}),
    }
    values.update(changes)
    return StrategyEvaluationComparison(**values)  # type: ignore[arg-type]


def test_comparison_preserves_order_and_is_immutable() -> None:
    comparison = make_comparison()
    assert comparison.candidate_evaluation_ids == ("candidate-1", "candidate-2")
    with pytest.raises(AttributeError):
        comparison.comparison_id = "changed"


def test_comparison_rejects_an_empty_candidate_identifier():
    with pytest.raises(InvalidStrategyEvaluationComparisonError):
        make_comparison(candidate_evaluation_ids=("",))


@pytest.mark.parametrize(
    "changes",
    [
        {"comparison_id": ""},
        {"baseline_evaluation_id": ""},
        {"candidate_evaluation_ids": ()},
        {"candidate_evaluation_ids": ("baseline",)},
        {"candidate_evaluation_ids": ("candidate", "candidate")},
        {"comparison_method_id": ""},
        {"comparison_method_version": ""},
        {"result": {}},
    ],
)
def test_comparison_rejects_invalid_invariants(changes: dict[str, object]) -> None:
    with pytest.raises(InvalidStrategyEvaluationComparisonError):
        make_comparison(**changes)
