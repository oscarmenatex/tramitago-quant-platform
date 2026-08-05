"""Shared deterministic fixtures for the IT-027-005 contractual suites."""

from datetime import datetime, timezone

from quant_platform.strategy_evaluation import (
    PublicationLifecycleStatus,
    PublishedStrategyEvaluationComparisonLifecycleRecord,
    PublishedStrategyEvaluationLifecycleRecord,
)


UTC = timezone.utc
INITIAL_TIME = datetime(2024, 1, 1, tzinfo=UTC)


def evaluation_record(**changes: object) -> PublishedStrategyEvaluationLifecycleRecord:
    values: dict[str, object] = {
        "lifecycle_id": "evaluation-lifecycle-A",
        "publication_id": "evaluation-publication-A",
        "status": PublicationLifecycleStatus.ACTIVE,
        "previous_lifecycle_id": None,
        "successor_publication_id": None,
        "transitioned_at": INITIAL_TIME,
        "reason": None,
    }
    values.update(changes)
    return PublishedStrategyEvaluationLifecycleRecord(**values)  # type: ignore[arg-type]


def comparison_record(
    **changes: object,
) -> PublishedStrategyEvaluationComparisonLifecycleRecord:
    values: dict[str, object] = {
        "lifecycle_id": "comparison-lifecycle-A",
        "publication_id": "comparison-publication-A",
        "status": PublicationLifecycleStatus.ACTIVE,
        "previous_lifecycle_id": None,
        "successor_publication_id": None,
        "transitioned_at": INITIAL_TIME,
        "reason": None,
    }
    values.update(changes)
    return PublishedStrategyEvaluationComparisonLifecycleRecord(**values)  # type: ignore[arg-type]
