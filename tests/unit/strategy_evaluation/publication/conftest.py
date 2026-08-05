from datetime import date

from quant_platform.strategy_evaluation import (
    ComparisonResult,
    EvaluationContext,
    EvaluationCriteria,
    PublishedStrategyEvaluation,
    PublishedStrategyEvaluationComparison,
    Strategy,
    StrategyEvaluation,
    StrategyEvaluationComparison,
)


def evaluation(identity: str = "evaluation", *, result=None) -> StrategyEvaluation:
    criteria = EvaluationCriteria({"criterion": "demo"})
    return StrategyEvaluation(
        identity,
        Strategy("strategy", {"rule": "demo"}, criteria),
        EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 2), ("AAPL",), "daily", "normal", {}
        ),
        "knowledge",
        "1",
        result or {"value": {"nested": [1]}},
    )


def comparison(identity: str = "comparison") -> StrategyEvaluationComparison:
    return StrategyEvaluationComparison(
        identity,
        "baseline",
        ("candidate-1", "candidate-2"),
        "method",
        "1",
        ComparisonResult({"evidence": {"value": 1}}),
    )


def published_evaluation(
    publication_id: str = "publication", evaluation_id: str = "evaluation"
) -> PublishedStrategyEvaluation:
    source = evaluation(evaluation_id)
    return PublishedStrategyEvaluation(
        publication_id,
        source.id,
        source.strategy.id,
        source.knowledge_id,
        source.knowledge_version,
        source.context,
        source.strategy.criteria,
        source.result,
    )


def published_comparison(
    publication_id: str = "publication", comparison_id: str = "comparison"
) -> PublishedStrategyEvaluationComparison:
    source = comparison(comparison_id)
    return PublishedStrategyEvaluationComparison(
        publication_id,
        source.id,
        source.baseline_evaluation_id,
        source.candidate_evaluation_ids,
        source.comparison_method_id,
        source.comparison_method_version,
        source.result,
    )
