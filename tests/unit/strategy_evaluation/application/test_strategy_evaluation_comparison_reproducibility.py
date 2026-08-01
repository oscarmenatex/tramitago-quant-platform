from datetime import date

from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluation,
)
from quant_platform.strategy_evaluation.application import (
    StrategyEvaluationComparisonService,
)
from quant_platform.strategy_evaluation.domain import ComparisonResult
from quant_platform.strategy_evaluation.registry import (
    StrategyEvaluationComparisonRegistry,
)


class Access:
    def __init__(self, *items):
        self.items = {item.id: item for item in items}

    def get(self, identity):
        return self.items[identity]


class Comparator:
    def compare(
        self, *, baseline, candidates, comparison_method_id, comparison_method_version
    ):
        return ComparisonResult(
            {
                "baseline": baseline.id,
                "candidates": tuple(item.id for item in candidates),
                "values": tuple(item.result["value"] for item in candidates),
            }
        )


def evaluation(identity, value=1):
    criteria = EvaluationCriteria({"kind": "stub"})
    return StrategyEvaluation(
        identity,
        Strategy(identity, {"rule": "stub"}, criteria),
        EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 2), ("AAPL",), "daily", "normal", {}
        ),
        "knowledge",
        "1",
        {"value": value},
    )


def compare(
    comparison_id="comparison",
    candidates=("first", "second"),
    values=(1, 2),
    version="1",
):
    baseline, first, second = (
        evaluation("baseline"),
        evaluation("first", values[0]),
        evaluation("second", values[1]),
    )
    return StrategyEvaluationComparisonService(
        Comparator(),
        StrategyEvaluationComparisonRegistry(),
        Access(baseline, first, second),
    ).compare(
        comparison_id=comparison_id,
        baseline_evaluation_id="baseline",
        candidate_evaluation_ids=candidates,
        comparison_method_id="stub",
        comparison_method_version=version,
    )


def test_rp_001_same_inputs_produce_equivalent_result():
    assert compare("one").result == compare("two").result


def test_rp_002_candidate_order_is_preserved():
    assert compare(candidates=("second", "first")).candidate_evaluation_ids == (
        "second",
        "first",
    )


def test_rp_003_comparison_method_version_is_preserved():
    assert compare(version="2").comparison_method_version == "2"


def test_rp_004_changed_evaluation_changes_deterministic_result():
    assert compare(values=(1, 2)).result != compare(values=(3, 2)).result


def test_rp_005_changed_comparison_id_does_not_change_technical_result():
    assert compare("one").result == compare("two").result
