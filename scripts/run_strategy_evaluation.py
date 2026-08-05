"""Run a local deterministic demonstration of Strategy Evaluation."""

from datetime import date, datetime, timezone
from types import SimpleNamespace
from typing import Any

from quant_platform.research.knowledge.consumption import KnowledgeConsumptionRecord
from quant_platform.strategy_evaluation import (
    ComparisonResult,
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluationAccess,
    StrategyEvaluationComparisonAccess,
    StrategyEvaluationComparisonRegistry,
    StrategyEvaluationComparisonService,
    StrategyEvaluationComparisonPublicationAccess,
    StrategyEvaluationComparisonPublicationRegistry,
    StrategyEvaluationComparisonPublicationService,
    StrategyEvaluationComparisonPublicationLifecycleService,
    PublishedStrategyEvaluationComparisonLifecycleAccess,
    PublishedStrategyEvaluationComparisonLifecycleRegistry,
    StrategyEvaluationRegistry,
    StrategyEvaluationService,
    StrategyEvaluationPublicationAccess,
    StrategyEvaluationPublicationRegistry,
    StrategyEvaluationPublicationService,
    StrategyEvaluationPublicationLifecycleService,
    PublishedStrategyEvaluationLifecycleAccess,
    PublishedStrategyEvaluationLifecycleRegistry,
    PublicationLifecycleStatus,
    ResolutionContext,
    StrategyEvaluationPublicationResolutionService,
)
from quant_platform.strategy_evaluation.domain.exceptions import (
    AmbiguousPublicationResolutionError,
    PublicationNotFoundError,
    PublicationNotResolvableError,
)


class InMemoryKnowledgeConsumptionAccess:
    """Local stand-in implementing the public exact-resolution operation."""

    def __init__(self, knowledge: KnowledgeConsumptionRecord) -> None:
        self._knowledge = knowledge

    def resolve(
        self, knowledge_id: str, knowledge_version: str
    ) -> KnowledgeConsumptionRecord:
        if (
            knowledge_id != self._knowledge.knowledge_id
            or knowledge_version != self._knowledge.version
        ):
            raise ValueError(
                f"Unknown published Knowledge '{knowledge_id}' version "
                f"'{knowledge_version}'."
            )
        return self._knowledge


class DeterministicDemoEvaluator:
    """Non-financial evaluator stub used only by this demonstration."""

    def evaluate(self, **_: Any) -> dict[str, str]:
        return {"evaluation_kind": "deterministic-demo-stub"}


class DeterministicDemoComparator:
    """Non-financial comparison stub used only by this demonstration."""

    def compare(self, **values: Any) -> ComparisonResult:
        return ComparisonResult(
            {
                "baseline_evaluation_id": values["baseline"].evaluation_id,
                "candidate_evaluation_ids": tuple(
                    candidate.evaluation_id for candidate in values["candidates"]
                ),
            }
        )


def main() -> None:
    criteria = EvaluationCriteria({"classification": "demonstration"})
    strategy = Strategy("strategy-demo", {"rule": "demonstration"}, criteria)
    context = EvaluationContext(
        date(2024, 1, 1),
        date(2024, 1, 31),
        ("AAPL",),
        "daily",
        "normal",
        {},
    )
    registry = StrategyEvaluationRegistry()
    service = StrategyEvaluationService(
        DeterministicDemoEvaluator(),
        registry,
        InMemoryKnowledgeConsumptionAccess(
            KnowledgeConsumptionRecord(
                knowledge_id="knowledge-demo",
                knowledge_version_id="KV-demo-001",
                knowledge_type="Pattern",
                description="Deterministic demo knowledge",
                status="VALIDATED",
                confidence_reference=None,
                relationship_references=(),
                source_reference="result-demo",
                version="1",
                created_at=None,
            )
        ),
    )

    baseline = service.evaluate(
        evaluation_id="evaluation-demo-baseline",
        strategy=strategy,
        context=context,
        criteria=criteria,
        knowledge_id="knowledge-demo",
        knowledge_version="1",
    )
    candidates = tuple(
        service.evaluate(
            evaluation_id=evaluation_id,
            strategy=Strategy(strategy_id, {"rule": "demonstration"}, criteria),
            context=context,
            criteria=criteria,
            knowledge_id="knowledge-demo",
            knowledge_version="1",
        )
        for evaluation_id, strategy_id in (
            ("evaluation-demo-candidate-001", "strategy-demo-candidate-001"),
            ("evaluation-demo-candidate-002", "strategy-demo-candidate-002"),
        )
    )
    evaluation_access = StrategyEvaluationAccess(registry)
    comparison_registry = StrategyEvaluationComparisonRegistry()
    created = StrategyEvaluationComparisonService(
        DeterministicDemoComparator(), comparison_registry, evaluation_access
    ).compare(
        comparison_id="comparison-demo-001",
        baseline_evaluation_id=baseline.evaluation_id,
        candidate_evaluation_ids=tuple(candidate.evaluation_id for candidate in candidates),
        comparison_method_id="deterministic-demo",
        comparison_method_version="1.0",
    )
    comparison_access = StrategyEvaluationComparisonAccess(comparison_registry)
    assert comparison_access.get(created.id) == created

    evaluation_publication_registry = StrategyEvaluationPublicationRegistry()
    evaluation_publication_access = StrategyEvaluationPublicationAccess(
        evaluation_publication_registry
    )
    published_evaluation = StrategyEvaluationPublicationService(
        evaluation_publication_registry, evaluation_access
    ).publish(
        publication_id="published-evaluation-demo-001",
        evaluation_id="evaluation-demo-baseline",
    )
    comparison_publication_registry = StrategyEvaluationComparisonPublicationRegistry()
    comparison_publication_access = StrategyEvaluationComparisonPublicationAccess(
        comparison_publication_registry
    )
    published_comparison = StrategyEvaluationComparisonPublicationService(
        comparison_publication_registry, comparison_access
    ).publish(
        publication_id="published-comparison-demo-001",
        comparison_id="comparison-demo-001",
    )
    published_evaluation_successor = StrategyEvaluationPublicationService(
        evaluation_publication_registry, evaluation_access
    ).publish(
        publication_id="publication-evaluation-B",
        evaluation_id="evaluation-demo-candidate-001",
    )
    evaluation_lifecycle_registry = PublishedStrategyEvaluationLifecycleRegistry()
    evaluation_lifecycle_access = PublishedStrategyEvaluationLifecycleAccess(
        evaluation_lifecycle_registry
    )
    evaluation_lifecycle_service = StrategyEvaluationPublicationLifecycleService(
        evaluation_publication_access, evaluation_lifecycle_registry
    )
    comparison_lifecycle_registry = PublishedStrategyEvaluationComparisonLifecycleRegistry()
    comparison_lifecycle_access = PublishedStrategyEvaluationComparisonLifecycleAccess(
        comparison_lifecycle_registry
    )
    comparison_lifecycle_service = StrategyEvaluationComparisonPublicationLifecycleService(
        comparison_publication_access, comparison_lifecycle_registry
    )
    initial_time = datetime(2024, 2, 1, tzinfo=timezone.utc)
    evaluation_lifecycle_service.register_initial(
        lifecycle_id="evaluation-lifecycle-A-active",
        publication_id="published-evaluation-demo-001",
        transitioned_at=initial_time,
    )
    evaluation_lifecycle_service.register_initial(
        lifecycle_id="evaluation-lifecycle-B-active",
        publication_id="publication-evaluation-B",
        transitioned_at=initial_time,
    )
    evaluation_lifecycle_service.supersede(
        lifecycle_id="evaluation-lifecycle-A-superseded",
        publication_id="published-evaluation-demo-001",
        successor_publication_id="publication-evaluation-B",
        transitioned_at=datetime(2024, 2, 2, tzinfo=timezone.utc),
        reason="Successor evaluation publication is active.",
    )
    comparison_lifecycle_service.register_initial(
        lifecycle_id="comparison-lifecycle-A-active",
        publication_id="published-comparison-demo-001",
        transitioned_at=initial_time,
    )
    resolution = StrategyEvaluationPublicationResolutionService(
        evaluation_publication_access,
        comparison_publication_access,
        evaluation_lifecycle_access,
        comparison_lifecycle_access,
    )
    active_comparison = resolution.resolve(
        ResolutionContext.for_comparison("comparison-demo-001")
    )
    assert active_comparison.publication is published_comparison
    comparison_lifecycle_service.withdraw(
        lifecycle_id="comparison-lifecycle-A-withdrawn",
        publication_id="published-comparison-demo-001",
        transitioned_at=datetime(2024, 2, 2, tzinfo=timezone.utc),
        reason="Comparison withdrawn from operational consumption.",
    )
    assert [record.status for record in evaluation_lifecycle_access.history(
        "published-evaluation-demo-001"
    )] == [PublicationLifecycleStatus.ACTIVE, PublicationLifecycleStatus.SUPERSEDED]
    assert evaluation_lifecycle_access.get_current(
        "published-evaluation-demo-001"
    ).status is PublicationLifecycleStatus.SUPERSEDED
    assert [record.status for record in comparison_lifecycle_access.history(
        "published-comparison-demo-001"
    )] == [PublicationLifecycleStatus.ACTIVE, PublicationLifecycleStatus.WITHDRAWN]
    assert comparison_lifecycle_access.get_current(
        "published-comparison-demo-001"
    ).status is PublicationLifecycleStatus.WITHDRAWN
    assert evaluation_publication_access.get("published-evaluation-demo-001") is published_evaluation
    assert evaluation_publication_access.get("publication-evaluation-B") is published_evaluation_successor
    assert comparison_publication_access.get("published-comparison-demo-001") is published_comparison
    assert evaluation_publication_access.get(
        "published-evaluation-demo-001"
    ) == published_evaluation
    assert evaluation_publication_access.resolve(
        "evaluation-demo-baseline"
    ) == published_evaluation
    assert evaluation_publication_access.get(
        "published-evaluation-demo-001"
    ) is published_evaluation
    assert evaluation_publication_access.resolve(
        "evaluation-demo-baseline"
    ) is published_evaluation
    assert comparison_publication_access.get(
        "published-comparison-demo-001"
    ) == published_comparison
    assert comparison_publication_access.resolve(
        "comparison-demo-001"
    ) == published_comparison
    assert comparison_publication_access.get(
        "published-comparison-demo-001"
    ) is published_comparison
    assert comparison_publication_access.resolve(
        "comparison-demo-001"
    ) is published_comparison
    active_evaluation = resolution.resolve(
        ResolutionContext.for_evaluation("evaluation-demo-candidate-001")
    )
    assert active_evaluation.publication is published_evaluation_successor
    for context in (
        ResolutionContext.for_evaluation("evaluation-demo-baseline"),
        ResolutionContext.for_comparison("comparison-demo-001"),
    ):
        with_exception = False
        try:
            resolution.resolve(context)
        except PublicationNotResolvableError:
            with_exception = True
        assert with_exception
    try:
        resolution.resolve(ResolutionContext.for_evaluation("missing"))
    except PublicationNotFoundError:
        pass
    else:
        raise AssertionError("Missing publication must not resolve.")
    assert resolution.resolve(ResolutionContext.for_evaluation("evaluation-demo-candidate-001")) == active_evaluation

    duplicate = type(published_evaluation_successor)(
        "publication-evaluation-duplicate",
        published_evaluation_successor.evaluation_id,
        published_evaluation_successor.strategy_id,
        published_evaluation_successor.knowledge_id,
        published_evaluation_successor.knowledge_version,
        published_evaluation_successor.context,
        published_evaluation_successor.criteria,
        published_evaluation_successor.result,
    )

    class DemoPublicationAccess:
        def list(self):
            return (published_evaluation_successor, duplicate)

    class DemoLifecycleAccess:
        def has_lifecycle(self, publication_id):
            return True

        def get_current(self, publication_id):
            return SimpleNamespace(status=PublicationLifecycleStatus.ACTIVE)

    ambiguous = StrategyEvaluationPublicationResolutionService(
        DemoPublicationAccess(), comparison_publication_access,
        DemoLifecycleAccess(), comparison_lifecycle_access,
    )
    try:
        ambiguous.resolve(ResolutionContext.for_evaluation("evaluation-demo-candidate-001"))
    except AmbiguousPublicationResolutionError:
        pass
    else:
        raise AssertionError("Multiple active publications must be ambiguous.")
    forbidden_fields = {
        "ranking",
        "winner",
        "recommendation",
        "approval",
        "capital_allocation",
    }
    assert not forbidden_fields.intersection(published_evaluation.__dataclass_fields__)
    assert not forbidden_fields.intersection(published_comparison.__dataclass_fields__)
    assert published_comparison.baseline_evaluation_id == "evaluation-demo-baseline"
    assert published_comparison.candidate_evaluation_ids == (
        "evaluation-demo-candidate-001",
        "evaluation-demo-candidate-002",
    )
    assert published_comparison.comparison_method_id == "deterministic-demo"
    assert published_comparison.comparison_method_version == "1.0"
    print(f"evaluation_publication_id: {published_evaluation.publication_id}")
    print(f"evaluation_id: {published_evaluation.evaluation_id}")
    print(f"strategy_id: {published_evaluation.strategy_id}")
    print(f"knowledge_id: {published_evaluation.knowledge_id}")
    print(f"knowledge_version: {published_evaluation.knowledge_version}")
    print(f"comparison_publication_id: {published_comparison.publication_id}")
    print(f"comparison_id: {published_comparison.comparison_id}")
    print(f"baseline_evaluation_id: {published_comparison.baseline_evaluation_id}")
    print(f"candidate_evaluation_ids: {published_comparison.candidate_evaluation_ids}")
    print(f"comparison_method_id: {published_comparison.comparison_method_id}")
    print(f"comparison_method_version: {published_comparison.comparison_method_version}")


if __name__ == "__main__":
    main()
