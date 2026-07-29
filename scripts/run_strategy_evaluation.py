"""Run a local deterministic demonstration of Strategy Evaluation."""

from datetime import date
from typing import Any

from quant_platform.research.knowledge.consumption import KnowledgeConsumptionRecord
from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluationAccess,
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

    service.evaluate(
        evaluation_id="evaluation-demo",
        strategy=strategy,
        context=context,
        criteria=criteria,
        knowledge_id="knowledge-demo",
        knowledge_version="1",
    )
    evaluation = StrategyEvaluationAccess(registry).get("evaluation-demo")
    print(f"evaluation_id: {evaluation.evaluation_id}")
    print(f"strategy_id: {evaluation.strategy.strategy_id}")
    print(f"knowledge_id: {evaluation.knowledge_id}")
    print(f"knowledge_version: {evaluation.knowledge_version}")
    print(f"result: {dict(evaluation.result)}")


if __name__ == "__main__":
    main()
