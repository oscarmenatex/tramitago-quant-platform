from dataclasses import FrozenInstanceError
from datetime import datetime
from pathlib import Path

import pytest

from quant_platform.data.access import DatasetAccess
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry
from quant_platform.research import ResearchRegistry
from quant_platform.research.configuration import ResearchConfigurationRegistry
from quant_platform.research.execution.research_execution_registry import (
    ResearchExecutionRegistry,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.consumption import KnowledgeConsumptionAccess
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_access import (
    ResearchKnowledgeRelationshipAccess,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_registry import (
    ResearchKnowledgeRelationshipRegistry,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_access import (
    ResearchValidatedKnowledgeAccess,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)


def build_consumption_access() -> (
    tuple[KnowledgeConsumptionAccess, ResearchValidatedKnowledgeRegistry]
):
    datasets = DatasetRegistry()
    report = MarketDataQualityChecker().check(
        [MarketData("AAPL", datetime(2024, 1, 2), 100, 105, 99, 104, 1_000)]
    )
    datasets.register("dataset-consumption", "AAPL", "v1", "synthetic", report)
    dataset_access = DatasetAccess(datasets)
    research = ResearchRegistry(dataset_access)
    configurations = ResearchConfigurationRegistry(research)
    executions = ResearchExecutionRegistry(configurations, research, dataset_access)
    results = ResearchResultRegistry(executions)
    research.register(
        "research-consumption", "Consumption", "test", "dataset-consumption", "v1"
    )
    configurations.register(
        "cfg-consumption", "research-consumption", "read-only", "test"
    )
    for suffix in ("a", "b"):
        executions.register(f"exec-{suffix}", "cfg-consumption")
        executions.start(f"exec-{suffix}")
        executions.complete(f"exec-{suffix}")
        results.register(f"result-{suffix}", f"exec-{suffix}")
    candidates = ResearchKnowledgeCandidateRegistry(results)
    validated = ResearchValidatedKnowledgeRegistry(candidates)
    for suffix in ("a", "b"):
        candidates.register(
            f"candidate-{suffix}", f"result-{suffix}", "Pattern", f"Knowledge {suffix}"
        )
        validated.register(
            f"knowledge-{suffix}",
            f"candidate-{suffix}",
            f"result-{suffix}",
            "Pattern",
            f"Knowledge {suffix}",
        )
    confidences = ResearchKnowledgeConfidenceRegistry(validated)
    confidences.register("confidence-a", "knowledge-a", "high")
    relationships = ResearchKnowledgeRelationshipRegistry(validated)
    relationships.register("relationship-a-b", "knowledge-a", "knowledge-b", "supports")
    return (
        KnowledgeConsumptionAccess(
            ResearchValidatedKnowledgeAccess(validated),
            ResearchKnowledgeConfidenceAccess(confidences),
            ResearchKnowledgeRelationshipAccess(relationships),
        ),
        validated,
    )


def test_get_publishes_only_the_public_knowledge_model() -> None:
    consumption, _ = build_consumption_access()
    knowledge = consumption.get("knowledge-a")
    assert knowledge.knowledge_id == "knowledge-a"
    assert knowledge.knowledge_type == "Pattern"
    assert knowledge.description == "Knowledge a"
    assert knowledge.status == "VALIDATED"
    assert knowledge.confidence_reference == "confidence-a"
    assert knowledge.relationship_references == ("relationship-a-b",)
    assert knowledge.source_reference == "result-a"
    assert knowledge.version == "1"
    assert knowledge.created_at is not None
    assert not hasattr(knowledge, "candidate_id")
    assert not hasattr(knowledge, "execution_id")
    assert not hasattr(knowledge, "dataset_id")


def test_existence_and_list_include_only_validated_knowledge() -> None:
    consumption, _ = build_consumption_access()
    assert consumption.exists("knowledge-a") is True
    assert consumption.exists("candidate-a") is False
    assert consumption.exists("missing") is False
    assert [knowledge.knowledge_id for knowledge in consumption.list()] == [
        "knowledge-a",
        "knowledge-b",
    ]


def test_get_rejects_unknown_or_candidate_knowledge() -> None:
    consumption, _ = build_consumption_access()
    for knowledge_id in ("", "candidate-a", "missing"):
        with pytest.raises(
            ValueError, match="knowledge_id is required|unknown reusable knowledge"
        ):
            consumption.get(knowledge_id)


def test_confidence_and_relationships_are_retrieved_without_mutation() -> None:
    consumption, validated = build_consumption_access()
    before = validated.get("knowledge-a")
    confidence = consumption.get_confidence("knowledge-a")
    relationships = consumption.get_relationships("knowledge-a")
    assert confidence is not None and confidence.confidence_reference == "confidence-a"
    assert [relationship.relationship_reference for relationship in relationships] == [
        "relationship-a-b"
    ]
    assert consumption.get_confidence("knowledge-b") is None
    assert before == validated.get("knowledge-a")


def test_consumption_results_are_immutable_public_views() -> None:
    consumption, _ = build_consumption_access()
    knowledge = consumption.get("knowledge-a")
    confidence = consumption.get_confidence("knowledge-a")
    relationship = consumption.get_relationships("knowledge-a")[0]
    with pytest.raises(FrozenInstanceError):
        knowledge.description = "changed"  # type: ignore[misc]
    assert confidence is not None
    with pytest.raises(FrozenInstanceError):
        confidence.confidence_level = "LOW"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        relationship.relationship_type = "REFINES"  # type: ignore[misc]


def test_associated_queries_reject_unknown_knowledge() -> None:
    consumption, _ = build_consumption_access()
    with pytest.raises(ValueError, match="unknown reusable knowledge"):
        consumption.get_confidence("missing")
    with pytest.raises(ValueError, match="unknown reusable knowledge"):
        consumption.get_relationships("missing")


def test_consumption_boundary_does_not_import_lifecycle_internals() -> None:
    source = Path(
        "src/quant_platform/research/knowledge/consumption/"
        "knowledge_consumption_access.py"
    ).read_text(encoding="utf-8")
    forbidden_dependencies = (
        "candidate.research_knowledge_candidate_registry",
        "validation.research_knowledge_validation_service",
        "confidence.research_knowledge_confidence_service",
        "relationship.research_knowledge_relationship_registry",
        "research_result_registry",
        "dataset_registry",
        "decision_engine",
    )
    assert not any(dependency in source for dependency in forbidden_dependencies)
