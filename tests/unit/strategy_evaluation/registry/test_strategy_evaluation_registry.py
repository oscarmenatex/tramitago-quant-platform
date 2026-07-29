from datetime import date

import pytest

from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluation,
    StrategyEvaluationRegistry,
)
from quant_platform.strategy_evaluation.domain import DuplicateStrategyEvaluationError


def make_evaluation(evaluation_id: str = "evaluation-001") -> StrategyEvaluation:
    criteria = EvaluationCriteria({"style": "stub"})
    return StrategyEvaluation(
        evaluation_id=evaluation_id,
        strategy=Strategy("strategy-001", {"rule": "stub"}, criteria),
        context=EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 31), ("AAPL",), "daily", "normal", {}
        ),
        knowledge_id="knowledge-001",
        knowledge_version="1",
        result={"status": "stub"},
    )


def test_registry_registers_and_returns_the_exact_accepted_instance() -> None:
    registry = StrategyEvaluationRegistry()
    evaluation = make_evaluation()

    assert registry.register(evaluation) is evaluation
    assert registry.get(evaluation.evaluation_id) is evaluation
    assert registry.exists(evaluation.evaluation_id) is True


def test_registry_rejects_duplicate_evaluation_id() -> None:
    registry = StrategyEvaluationRegistry()
    registry.register(make_evaluation())

    with pytest.raises(DuplicateStrategyEvaluationError):
        registry.register(make_evaluation())


def test_registry_list_is_an_immutable_snapshot() -> None:
    registry = StrategyEvaluationRegistry()
    evaluation = make_evaluation()
    registry.register(evaluation)

    registered = registry.list()

    assert registered == (evaluation,)
    with pytest.raises(AttributeError):
        registered.append(evaluation)  # type: ignore[attr-defined]
