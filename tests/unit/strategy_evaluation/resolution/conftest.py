"""Deterministic fixtures for IT-027-006 resolution evidence."""

from datetime import datetime, timezone

import pytest

from datetime import date

from quant_platform.strategy_evaluation import (
    ComparisonResult,
    EvaluationContext,
    EvaluationCriteria,
    PublishedStrategyEvaluationComparisonLifecycleAccess,
    PublishedStrategyEvaluationComparisonLifecycleRecord,
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    PublishedStrategyEvaluationLifecycleAccess,
    PublishedStrategyEvaluationLifecycleRecord,
    PublishedStrategyEvaluationLifecycleRegistry,
    PublicationLifecycleStatus,
    StrategyEvaluationComparisonPublicationAccess,
    StrategyEvaluationComparisonPublicationRegistry,
    StrategyEvaluationPublicationAccess,
    StrategyEvaluationPublicationRegistry,
    PublishedStrategyEvaluation,
    PublishedStrategyEvaluationComparison,
    Strategy,
    StrategyEvaluation,
    StrategyEvaluationComparison,
)


UTC = timezone.utc
TIME = datetime(2024, 1, 1, tzinfo=UTC)


def published_evaluation(publication_id="publication", evaluation_id="evaluation"):
    criteria = EvaluationCriteria({"criterion": "demo"})
    source = StrategyEvaluation(
        evaluation_id,
        Strategy("strategy", {"rule": "demo"}, criteria),
        EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 2), ("AAPL",), "daily", "normal", {}
        ),
        "knowledge",
        "1",
        {"value": {"nested": [1]}},
    )
    return PublishedStrategyEvaluation(
        publication_id, source.id, source.strategy.id, source.knowledge_id,
        source.knowledge_version, source.context, source.strategy.criteria, source.result,
    )


def published_comparison(publication_id="publication", comparison_id="comparison"):
    source = StrategyEvaluationComparison(
        comparison_id, "baseline", ("candidate-1",), "method", "1",
        ComparisonResult({"evidence": {"value": 1}}),
    )
    return PublishedStrategyEvaluationComparison(
        publication_id, source.id, source.baseline_evaluation_id,
        source.candidate_evaluation_ids, source.comparison_method_id,
        source.comparison_method_version, source.result,
    )


@pytest.fixture
def boundaries():
    evaluation_registry = StrategyEvaluationPublicationRegistry()
    comparison_registry = StrategyEvaluationComparisonPublicationRegistry()
    evaluation_lifecycle_registry = PublishedStrategyEvaluationLifecycleRegistry()
    comparison_lifecycle_registry = (
        PublishedStrategyEvaluationComparisonLifecycleRegistry()
    )
    return (
        StrategyEvaluationPublicationAccess(evaluation_registry),
        StrategyEvaluationComparisonPublicationAccess(comparison_registry),
        PublishedStrategyEvaluationLifecycleAccess(evaluation_lifecycle_registry),
        PublishedStrategyEvaluationComparisonLifecycleAccess(
            comparison_lifecycle_registry
        ),
        evaluation_registry,
        comparison_registry,
        evaluation_lifecycle_registry,
        comparison_lifecycle_registry,
    )


def active_evaluation(registry, lifecycle_registry, source_id="evaluation-A"):
    publication = published_evaluation("publication-evaluation-A", source_id)
    registry.register(publication)
    lifecycle_registry.append(
        PublishedStrategyEvaluationLifecycleRecord(
            "lifecycle-evaluation-A", publication.publication_id,
            PublicationLifecycleStatus.ACTIVE, None, None, TIME, None,
        )
    )
    return publication


def active_comparison(registry, lifecycle_registry, source_id="comparison-A"):
    publication = published_comparison("publication-comparison-A", source_id)
    registry.register(publication)
    lifecycle_registry.append(
        PublishedStrategyEvaluationComparisonLifecycleRecord(
            "lifecycle-comparison-A", publication.publication_id,
            PublicationLifecycleStatus.ACTIVE, None, None, TIME, None,
        )
    )
    return publication
