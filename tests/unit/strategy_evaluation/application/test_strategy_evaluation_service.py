from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest

from quant_platform.research.knowledge.consumption import KnowledgeConsumptionRecord
from quant_platform.strategy_evaluation import (
    EvaluationContext,
    EvaluationCriteria,
    Strategy,
    StrategyEvaluationRegistry,
    StrategyEvaluationService,
)
from quant_platform.strategy_evaluation.domain import (
    DuplicateStrategyEvaluationError,
    InvalidEvaluationIdentityError,
    InvalidEvaluationInputError,
    InvalidEvaluationResultError,
    KnowledgeNotFoundError,
    StrategyEvaluatorExecutionError,
)


def published_knowledge(
    knowledge_id: str, knowledge_version: str, status: str = "VALIDATED"
) -> KnowledgeConsumptionRecord:
    return KnowledgeConsumptionRecord(
        knowledge_id=knowledge_id,
        knowledge_version_id=f"KV-{knowledge_id}-{knowledge_version}",
        knowledge_type="Pattern",
        description="Published test knowledge",
        status=status,
        confidence_reference=None,
        relationship_references=(),
        source_reference="result-test",
        version=knowledge_version,
        created_at=None,
    )


class InMemoryKnowledgeConsumptionAccess:
    def __init__(self, knowledge: KnowledgeConsumptionRecord | None) -> None:
        self.knowledge = knowledge
        self.requests: list[str] = []

    def resolve(
        self, knowledge_id: str, knowledge_version: str
    ) -> KnowledgeConsumptionRecord:
        self.requests.append(f"{knowledge_id}/{knowledge_version}")
        if (
            self.knowledge is None
            or self.knowledge.knowledge_id != knowledge_id
            or self.knowledge.version != knowledge_version
            or self.knowledge.status != "VALIDATED"
        ):
            raise ValueError("unknown published knowledge")
        return self.knowledge


class DeterministicEvaluator:
    def __init__(self, result: object = None) -> None:
        self.result = {"kind": "deterministic-stub"} if result is None else result
        self.calls = 0
        self.received_knowledge: object | None = None

    def evaluate(self, **values: object) -> object:
        self.calls += 1
        self.received_knowledge = values["knowledge"]
        return self.result


class FailingEvaluator:
    def evaluate(self, **_: object) -> object:
        raise RuntimeError("calculation failed")


def inputs() -> dict[str, Any]:
    criteria = EvaluationCriteria({"style": "stub"})
    return {
        "evaluation_id": "evaluation-001",
        "strategy": Strategy("strategy-001", {"rule": "stub"}, criteria),
        "context": EvaluationContext(
            date(2024, 1, 1), date(2024, 1, 31), ("AAPL",), "daily", "normal", {}
        ),
        "criteria": criteria,
        "knowledge_id": "knowledge-001",
        "knowledge_version": "1",
    }


def build_service(
    evaluator: object | None = None,
    knowledge_version: str = "1",
    knowledge_status: str = "VALIDATED",
) -> tuple[StrategyEvaluationService, StrategyEvaluationRegistry, object]:
    registry = StrategyEvaluationRegistry()
    evaluator = DeterministicEvaluator() if evaluator is None else evaluator
    access = InMemoryKnowledgeConsumptionAccess(
        published_knowledge("knowledge-001", knowledge_version, knowledge_status)
    )
    return StrategyEvaluationService(evaluator, registry, access), registry, evaluator


def test_service_evaluates_registers_and_preserves_traceability() -> None:
    service, registry, evaluator = build_service()

    evaluation = service.evaluate(**inputs())

    assert registry.get("evaluation-001") is evaluation
    assert evaluation.strategy.id == "strategy-001"
    assert evaluation.knowledge_id == "knowledge-001"
    assert evaluation.knowledge_version == "1"
    assert evaluation.result == {"kind": "deterministic-stub"}
    assert evaluator.calls == 1
    assert isinstance(evaluator.received_knowledge, KnowledgeConsumptionRecord)
    assert evaluator.received_knowledge is service._knowledge_access.knowledge  # type: ignore[attr-defined]


def test_duplicate_is_rejected_before_resolution_or_evaluator_runs() -> None:
    service, _, evaluator = build_service()
    service.evaluate(**inputs())

    with pytest.raises(DuplicateStrategyEvaluationError):
        service.evaluate(**inputs())

    assert evaluator.calls == 1
    assert service._knowledge_access.requests == ["knowledge-001/1"]  # type: ignore[attr-defined]


@pytest.mark.parametrize("evaluation_id", ["", "   ", 1])
def test_invalid_evaluation_identity_is_rejected(evaluation_id: object) -> None:
    service, registry, _ = build_service()
    values = inputs()
    values["evaluation_id"] = evaluation_id

    with pytest.raises(InvalidEvaluationIdentityError):
        service.evaluate(**values)

    assert registry.list() == ()


def test_missing_knowledge_is_translated_without_partial_registration() -> None:
    service, registry, _ = build_service()
    values = inputs()
    values["knowledge_id"] = "missing"

    with pytest.raises(KnowledgeNotFoundError) as raised:
        service.evaluate(**values)

    assert isinstance(raised.value.__cause__, ValueError)
    assert registry.list() == ()


def test_missing_knowledge_version_is_translated_without_evaluator_or_registration() -> None:
    service, registry, _ = build_service(knowledge_version="2")

    with pytest.raises(KnowledgeNotFoundError):
        service.evaluate(**inputs())

    assert registry.list() == ()


def test_non_consumable_knowledge_version_never_runs_evaluator_or_registers() -> None:
    evaluator = DeterministicEvaluator()
    service, registry, _ = build_service(evaluator, knowledge_status="CREATED")

    with pytest.raises(KnowledgeNotFoundError):
        service.evaluate(**inputs())

    assert evaluator.calls == 0
    assert registry.list() == ()


def test_two_versions_of_one_lineage_are_resolved_as_distinct_evaluations() -> None:
    registry = StrategyEvaluationRegistry()
    evaluator = DeterministicEvaluator()
    access = InMemoryKnowledgeConsumptionAccess(
        published_knowledge("knowledge-001", "1")
    )
    service = StrategyEvaluationService(evaluator, registry, access)
    first = service.evaluate(**inputs())

    access.knowledge = published_knowledge("knowledge-001", "2")
    second_values = inputs()
    second_values["evaluation_id"] = "evaluation-002"
    second_values["knowledge_version"] = "2"
    second = service.evaluate(**second_values)

    assert (first.knowledge_id, first.knowledge_version) == ("knowledge-001", "1")
    assert (second.knowledge_id, second.knowledge_version) == ("knowledge-001", "2")
    assert access.requests == ["knowledge-001/1", "knowledge-001/2"]


def test_resolution_failure_never_runs_evaluator_or_registers() -> None:
    evaluator = DeterministicEvaluator()
    service, registry, _ = build_service(evaluator, knowledge_version="2")

    with pytest.raises(KnowledgeNotFoundError):
        service.evaluate(**inputs())

    assert evaluator.calls == 0
    assert registry.list() == ()


@pytest.mark.parametrize("result", [{}, ["not", "a", "mapping"]])
def test_invalid_evaluator_result_is_rejected(result: object) -> None:
    service, registry, _ = build_service(DeterministicEvaluator(result))

    with pytest.raises(InvalidEvaluationResultError):
        service.evaluate(**inputs())

    assert registry.list() == ()


def test_evaluator_failure_is_translated_without_partial_registration() -> None:
    service, registry, _ = build_service(FailingEvaluator())

    with pytest.raises(StrategyEvaluatorExecutionError) as raised:
        service.evaluate(**inputs())

    assert isinstance(raised.value.__cause__, RuntimeError)
    assert registry.list() == ()


def test_explicit_criteria_must_match_strategy_criteria() -> None:
    service, registry, _ = build_service()
    values = inputs()
    values["criteria"] = EvaluationCriteria({"style": "other"})

    with pytest.raises(InvalidEvaluationInputError):
        service.evaluate(**values)

    assert registry.list() == ()


def test_result_and_inputs_are_isolated_from_later_mutation() -> None:
    source = {"nested": ["original"]}
    evaluator = DeterministicEvaluator(source)
    service, _, _ = build_service(evaluator)
    values = inputs()
    evaluation = service.evaluate(**values)
    source["nested"].append("changed")

    assert evaluation.result == MappingProxyType({"nested": ("original",)})
    with pytest.raises(TypeError):
        evaluation.result["nested"] = ()  # type: ignore[index]


def test_same_deterministic_inputs_produce_same_result_with_new_identity() -> None:
    service, _, _ = build_service()
    first = service.evaluate(**inputs())
    second_inputs = inputs()
    second_inputs["evaluation_id"] = "evaluation-002"
    second = service.evaluate(**second_inputs)

    assert first.result == second.result


def test_service_uses_only_the_public_knowledge_consumption_boundary() -> None:
    source = Path(
        "src/quant_platform/strategy_evaluation/application/"
        "strategy_evaluation_service.py"
    ).read_text(encoding="utf-8")
    forbidden_dependencies = (
        "research_knowledge_candidate",
        "research_validated_knowledge",
        "research_knowledge_validation_service",
        "research_knowledge_confidence_service",
        "research_knowledge_relationship",
        "quant_platform.data",
        "quant_platform.research.result",
    )

    assert "research.knowledge.consumption import KnowledgeConsumptionAccess" in source
    assert not any(dependency in source for dependency in forbidden_dependencies)
