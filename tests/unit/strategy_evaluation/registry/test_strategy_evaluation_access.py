from datetime import date

from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluation,
    StrategyEvaluationAccess,
    StrategyEvaluationRegistry,
)


def test_access_exposes_only_read_operations() -> None:
    criteria = EvaluationCriteria({"style": "stub"})
    evaluation = StrategyEvaluation(
        "evaluation-001",
        Strategy("strategy-001", {"rule": "stub"}, criteria),
        EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 31), ("AAPL",), "daily", "normal", {}
        ),
        "knowledge-001",
        "1",
        {"status": "stub"},
    )
    registry = StrategyEvaluationRegistry()
    registry.register(evaluation)
    access = StrategyEvaluationAccess(registry)

    assert access.get("evaluation-001") is evaluation
    assert access.exists("evaluation-001") is True
    assert access.list() == (evaluation,)
    assert not hasattr(access, "register")
