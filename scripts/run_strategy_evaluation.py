"""Run a local deterministic demonstration of Strategy Evaluation."""

from datetime import date
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
    StrategyEvaluationRegistry,
    StrategyEvaluationService,
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
    evaluation = StrategyEvaluationAccess(registry).get(baseline.evaluation_id)
    print(f"evaluation_id: {evaluation.evaluation_id}")
    print(f"strategy_id: {evaluation.strategy.strategy_id}")
    print(f"knowledge_id: {evaluation.knowledge_id}")
    print(f"knowledge_version: {evaluation.knowledge_version}")
    print(f"result: {dict(evaluation.result)}")
    comparison_registry = StrategyEvaluationComparisonRegistry()
    created = StrategyEvaluationComparisonService(
        DeterministicDemoComparator(), comparison_registry, StrategyEvaluationAccess(registry)
    ).compare(
        comparison_id="comparison-demo-001",
        baseline_evaluation_id=baseline.evaluation_id,
        candidate_evaluation_ids=tuple(candidate.evaluation_id for candidate in candidates),
        comparison_method_id="deterministic-demo",
        comparison_method_version="1.0",
    )
    recovered = StrategyEvaluationComparisonAccess(comparison_registry).get(created.id)
    assert recovered == created
    assert recovered.baseline_evaluation_id == "evaluation-demo-baseline"
    assert recovered.candidate_evaluation_ids == (
        "evaluation-demo-candidate-001",
        "evaluation-demo-candidate-002",
    )
    assert recovered.comparison_method_id == "deterministic-demo"
    assert recovered.comparison_method_version == "1.0"
    print(f"comparison_id: {recovered.comparison_id}")
    print(f"baseline_evaluation_id: {recovered.baseline_evaluation_id}")
    print(f"candidate_evaluation_ids: {recovered.candidate_evaluation_ids}")
    print(f"comparison_method_id: {recovered.comparison_method_id}")
    print(f"comparison_method_version: {recovered.comparison_method_version}")
    print(f"comparison_result: {dict(recovered.result.values)}")


if __name__ == "__main__":
    main()
