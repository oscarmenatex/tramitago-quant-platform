from datetime import date

import pytest

from quant_platform.strategy_evaluation.domain import (
    EvaluationContext,
    EvaluationCriteria,
    InconsistentStrategyEvaluationError,
    Strategy,
    StrategyEvaluation,
)


def make_evaluation(**changes: object) -> StrategyEvaluation:
    values: dict[str, object] = {
        "evaluation_id": "evaluation-001",
        "strategy": Strategy(
            "strategy-001", {"rules": {"signal": "momentum"}}, EvaluationCriteria({"style": "momentum"})
        ),
        "context": EvaluationContext(
            date(2024, 1, 1), date(2024, 12, 31), ("AAPL",), "one_year", "mixed", {}
        ),
        "knowledge_id": "knowledge-42",
        "knowledge_version": "v3",
        "result": {"status": "evaluated", "summary": {"eligible": True}},
    }
    values.update(changes)
    return StrategyEvaluation(**values)  # type: ignore[arg-type]


def test_evaluation_links_complete_trace_and_freezes_its_result() -> None:
    evaluation = make_evaluation()

    assert evaluation.id == "evaluation-001"
    assert evaluation.strategy.id == "strategy-001"
    assert evaluation.context.asset_universe == ("AAPL",)
    assert evaluation.knowledge_id == "knowledge-42"
    assert evaluation.knowledge_version == "v3"
    with pytest.raises(TypeError):
        evaluation.result["summary"]["eligible"] = False


def test_domain_objects_are_isolated_from_mutable_input_structures() -> None:
    criteria_values = {"style": "momentum", "thresholds": [0.2]}
    strategy_definition = {"rules": {"signal": "momentum"}}
    restrictions = {"position_limits": {"max_weight": 0.1}}
    result = {"summary": {"eligible": True}}

    criteria = EvaluationCriteria(criteria_values)
    strategy = Strategy("strategy-001", strategy_definition, criteria)
    context = EvaluationContext(
        date(2024, 1, 1),
        date(2024, 12, 31),
        ("AAPL",),
        "one_year",
        "mixed",
        restrictions,
    )
    evaluation = StrategyEvaluation(
        "evaluation-001", strategy, context, "knowledge-42", "v3", result
    )

    criteria_values["thresholds"].append(0.3)
    strategy_definition["rules"]["signal"] = "value"
    restrictions["position_limits"]["max_weight"] = 0.5
    result["summary"]["eligible"] = False

    assert criteria.values["thresholds"] == (0.2,)
    assert strategy.definition["rules"]["signal"] == "momentum"
    assert context.restrictions["position_limits"]["max_weight"] == 0.1
    assert evaluation.result["summary"]["eligible"] is True


@pytest.mark.parametrize(
    "changes",
    [
        {"evaluation_id": ""},
        {"strategy": "strategy-001"},
        {"context": {}},
        {"knowledge_id": ""},
        {"knowledge_id": None},
        {"knowledge_version": ""},
        {"knowledge_version": None},
        {"result": {}},
    ],
)
def test_evaluation_rejects_incomplete_trace(changes: dict[str, object]) -> None:
    with pytest.raises(InconsistentStrategyEvaluationError):
        make_evaluation(**changes)


def test_evaluation_normalizes_opaque_knowledge_references() -> None:
    evaluation = make_evaluation(knowledge_id="  knowledge-42  ", knowledge_version=" v3 ")

    assert evaluation.knowledge_id == "knowledge-42"
    assert evaluation.knowledge_version == "v3"


@pytest.mark.parametrize("missing_field", ["knowledge_id", "knowledge_version"])
def test_evaluation_requires_both_knowledge_reference_fields(missing_field: str) -> None:
    values = {
        "evaluation_id": "evaluation-001",
        "strategy": make_evaluation().strategy,
        "context": make_evaluation().context,
        "knowledge_id": "knowledge-42",
        "knowledge_version": "v3",
        "result": {"status": "evaluated"},
    }
    del values[missing_field]

    with pytest.raises(TypeError):
        StrategyEvaluation(**values)  # type: ignore[arg-type]
