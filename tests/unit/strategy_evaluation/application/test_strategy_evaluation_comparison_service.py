from datetime import date

import pytest

from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluation,
)
from quant_platform.strategy_evaluation.domain import (
    ComparisonResult,
    IncompatibleEvaluationContextError,
    IncompatibleEvaluationCriteriaError,
    IncompatibleEvaluationResultError,
    IncompatibleKnowledgeReferenceError,
    InvalidComparisonRequestError,
    InvalidComparisonResultError,
    StrategyEvaluationComparisonExecutionError,
)
from quant_platform.strategy_evaluation.application import (
    StrategyEvaluationComparisonService,
)
from quant_platform.strategy_evaluation.registry import (
    StrategyEvaluationComparisonRegistry,
)


class Access:
    def __init__(self, *values):
        self.values = {value.id: value for value in values}
        self.calls = []

    def get(self, identity):
        self.calls.append(identity)
        return self.values[identity]


class Comparator:
    def __init__(self, result=None, error=None):
        self.result = result or ComparisonResult({"evidence": True})
        self.error = error
        self.call_count = 0
        self.calls = []

    def compare(self, **kwargs):
        self.call_count += 1
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


class Registry(StrategyEvaluationComparisonRegistry):
    def __init__(self):
        super().__init__()
        self.register_call_count = 0

    def register(self, comparison):
        self.register_call_count += 1
        return super().register(comparison)


def evaluation(identity, *, context=None, criteria=None, knowledge="1", result=None):
    criteria = criteria or EvaluationCriteria({"style": "x"})
    return StrategyEvaluation(
        identity,
        Strategy(f"strategy-{identity}", {"rule": "x"}, criteria),
        context
        or EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 2), ("AAPL",), "daily", "normal", {}
        ),
        "knowledge",
        knowledge,
        result or {"value": 1},
    )


def service(baseline, candidate, comparator=None, registry=None):
    comparator, registry = comparator or Comparator(), registry or Registry()
    return (
        StrategyEvaluationComparisonService(
            comparator, registry, Access(baseline, candidate)
        ),
        comparator,
        registry,
    )


def test_valid_flow_preserves_access_order_and_registers_once():
    baseline, candidate = evaluation("base"), evaluation("candidate")
    target, comparator, registry = service(baseline, candidate)
    result = target.compare(
        comparison_id="comparison",
        baseline_evaluation_id="base",
        candidate_evaluation_ids=("candidate",),
        comparison_method_id="stub",
        comparison_method_version="1",
    )
    assert comparator.call_count == registry.register_call_count == 1
    assert comparator.calls[0]["baseline"] is baseline and comparator.calls[0][
        "candidates"
    ] == (candidate,)
    assert result.result == ComparisonResult({"evidence": True})


@pytest.mark.parametrize(
    "candidate,error",
    [
        (
            evaluation(
                "candidate",
                context=EvaluationContext(
                    date(2024, 2, 1), date(2024, 2, 2), ("AAPL",), "daily", "normal", {}
                ),
            ),
            IncompatibleEvaluationContextError,
        ),
        (
            evaluation("candidate", criteria=EvaluationCriteria({"style": "y"})),
            IncompatibleEvaluationCriteriaError,
        ),
        (evaluation("candidate", knowledge="2"), IncompatibleKnowledgeReferenceError),
        (
            evaluation("candidate", result={"other": 1}),
            IncompatibleEvaluationResultError,
        ),
    ],
)
def test_incompatible_inputs_are_atomic(candidate, error):
    target, comparator, registry = service(evaluation("base"), candidate)
    with pytest.raises(error):
        target.compare(
            comparison_id="comparison",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert comparator.call_count == registry.register_call_count == 0


def test_invalid_request_and_comparator_failures_are_atomic_and_chained():
    target, comparator, registry = service(evaluation("base"), evaluation("candidate"))
    with pytest.raises(InvalidComparisonRequestError):
        target.compare(
            comparison_id="",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert comparator.call_count == registry.register_call_count == 0
    target, comparator, registry = service(
        evaluation("base"),
        evaluation("candidate"),
        Comparator(error=RuntimeError("boom")),
    )
    with pytest.raises(StrategyEvaluationComparisonExecutionError) as raised:
        target.compare(
            comparison_id="comparison",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert (
        isinstance(raised.value.__cause__, RuntimeError)
        and registry.register_call_count == 0
    )


def test_invalid_comparator_result_is_atomic():
    target, comparator, registry = service(
        evaluation("base"), evaluation("candidate"), Comparator(result=object())
    )
    with pytest.raises(InvalidComparisonResultError):
        target.compare(
            comparison_id="comparison",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert comparator.call_count == 1 and registry.register_call_count == 0


def test_duplicate_and_missing_evaluations_abort_before_comparator():
    registry = Registry()
    target, comparator, registry = service(
        evaluation("base"), evaluation("candidate"), registry=registry
    )
    registry._comparisons["existing"] = object()
    with pytest.raises(Exception):
        target.compare(
            comparison_id="existing",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert comparator.call_count == registry.register_call_count == 0
    target, comparator, registry = service(evaluation("base"), evaluation("candidate"))
    with pytest.raises(KeyError):
        target.compare(
            comparison_id="new",
            baseline_evaluation_id="missing",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert comparator.call_count == registry.register_call_count == 0


def test_domain_comparator_error_is_preserved_without_registration():
    domain_error = InvalidComparisonRequestError("domain")
    target, comparator, registry = service(
        evaluation("base"), evaluation("candidate"), Comparator(error=domain_error)
    )
    with pytest.raises(InvalidComparisonRequestError) as raised:
        target.compare(
            comparison_id="comparison",
            baseline_evaluation_id="base",
            candidate_evaluation_ids=("candidate",),
            comparison_method_id="stub",
            comparison_method_version="1",
        )
    assert (
        raised.value is domain_error
        and comparator.call_count == 1
        and registry.register_call_count == 0
    )
