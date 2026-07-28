from datetime import datetime

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
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_access import (
    ResearchKnowledgeRelationshipAccess,
)
from quant_platform.research.knowledge.relationship.research_knowledge_relationship_registry import (
    ResearchKnowledgeRelationshipRegistry,
)
from quant_platform.research.knowledge.validation.research_validated_knowledge_registry import (
    ResearchValidatedKnowledgeRegistry,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)


def build_available_dataset() -> DatasetRegistry:
    registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check(
        [
            MarketData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 2),
                open=100.0,
                high=105.0,
                low=99.0,
                close=104.0,
                volume=1_000_000.0,
            )
        ]
    )
    registry.register(
        dataset_id="dataset-relationship",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def build_relationship_environment() -> tuple[
    ResearchKnowledgeRelationshipRegistry,
    ResearchKnowledgeRelationshipAccess,
]:
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research_registry.register(
        research_id="research-relationship",
        name="Relationship test",
        objective="Test relationship workflow",
        dataset_id="dataset-relationship",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-relationship",
        research_id="research-relationship",
        access_policy="read-only",
        description="cfg",
    )
    exec_registry.register(
        execution_id="exec-relationship-a", configuration_id="cfg-relationship"
    )
    exec_registry.start("exec-relationship-a")
    exec_registry.complete("exec-relationship-a")
    result_registry.register(
        result_id="res-relationship-a", execution_id="exec-relationship-a"
    )

    exec_registry.register(
        execution_id="exec-relationship-b", configuration_id="cfg-relationship"
    )
    exec_registry.start("exec-relationship-b")
    exec_registry.complete("exec-relationship-b")
    result_registry.register(
        result_id="res-relationship-b", execution_id="exec-relationship-b"
    )

    candidate_registry = ResearchKnowledgeCandidateRegistry(result_registry)
    candidate_registry.register(
        knowledge_candidate_id="candidate-relationship-a",
        result_id="res-relationship-a",
        knowledge_type="Pattern",
        description="First candidate",
    )
    candidate_registry.register(
        knowledge_candidate_id="candidate-relationship-b",
        result_id="res-relationship-b",
        knowledge_type="Pattern",
        description="Second candidate",
    )

    validated_registry = ResearchValidatedKnowledgeRegistry(candidate_registry)
    validated_registry.register(
        validated_knowledge_id="validated-relationship-a",
        candidate_id="candidate-relationship-a",
        result_id="res-relationship-a",
        knowledge_type="Pattern",
        description="First validated",
    )
    validated_registry.register(
        validated_knowledge_id="validated-relationship-b",
        candidate_id="candidate-relationship-b",
        result_id="res-relationship-b",
        knowledge_type="Pattern",
        description="Second validated",
    )

    relationship_registry = ResearchKnowledgeRelationshipRegistry(validated_registry)
    access_layer = ResearchKnowledgeRelationshipAccess(relationship_registry)
    return relationship_registry, access_layer


def test_register_relationship_creates_record():
    registry, _ = build_relationship_environment()

    relation = registry.register(
        knowledge_relationship_id="relationship-1",
        source_knowledge_id="validated-relationship-a",
        target_knowledge_id="validated-relationship-b",
        relationship_type="supports",
    )

    assert relation.knowledge_relationship_id == "relationship-1"
    assert relation.source_knowledge_id == "validated-relationship-a"
    assert relation.target_knowledge_id == "validated-relationship-b"
    assert relation.relationship_type == "SUPPORTS"
    assert relation.created_at is not None


def test_register_relationship_rejects_unknown_knowledge():
    registry, _ = build_relationship_environment()

    with pytest.raises(ValueError, match="unknown source knowledge"):
        registry.register(
            knowledge_relationship_id="relationship-2",
            source_knowledge_id="missing-source",
            target_knowledge_id="validated-relationship-b",
            relationship_type="related_to",
        )


def test_register_relationship_rejects_self_reference():
    registry, _ = build_relationship_environment()

    with pytest.raises(ValueError, match="must be different"):
        registry.register(
            knowledge_relationship_id="relationship-3",
            source_knowledge_id="validated-relationship-a",
            target_knowledge_id="validated-relationship-a",
            relationship_type="refines",
        )


def test_register_relationship_rejects_duplicates():
    registry, _ = build_relationship_environment()

    registry.register(
        knowledge_relationship_id="relationship-4",
        source_knowledge_id="validated-relationship-a",
        target_knowledge_id="validated-relationship-b",
        relationship_type="related_to",
    )

    with pytest.raises(ValueError, match="already registered"):
        registry.register(
            knowledge_relationship_id="relationship-5",
            source_knowledge_id="validated-relationship-a",
            target_knowledge_id="validated-relationship-b",
            relationship_type="related_to",
        )


def test_get_and_list_relationships():
    registry, access = build_relationship_environment()

    relation = registry.register(
        knowledge_relationship_id="relationship-6",
        source_knowledge_id="validated-relationship-a",
        target_knowledge_id="validated-relationship-b",
        relationship_type="refines",
    )

    assert registry.get("relationship-6") == relation
    assert access.get("relationship-6") == relation
    assert access.exists("relationship-6") is True
    assert len(access.list()) == 1


def test_list_for_knowledge_returns_associated_relationships():
    registry, access = build_relationship_environment()

    registry.register(
        knowledge_relationship_id="relationship-7",
        source_knowledge_id="validated-relationship-a",
        target_knowledge_id="validated-relationship-b",
        relationship_type="specializes",
    )

    related = access.list_for_knowledge("validated-relationship-a")
    assert len(related) == 1
    assert related[0].target_knowledge_id == "validated-relationship-b"


def test_register_relationship_does_not_modify_validated_knowledge():
    registry, _ = build_relationship_environment()

    source = registry._knowledge_versions.get("validated-relationship-a")
    target = registry._knowledge_versions.get("validated-relationship-b")

    registry.register(
        knowledge_relationship_id="relationship-8",
        source_knowledge_id="validated-relationship-a",
        target_knowledge_id="validated-relationship-b",
        relationship_type="supports",
    )

    assert source is not None
    assert target is not None
    assert source.status == "VALIDATED"
    assert target.status == "VALIDATED"
    assert source.description == "First validated"
    assert target.description == "Second validated"
