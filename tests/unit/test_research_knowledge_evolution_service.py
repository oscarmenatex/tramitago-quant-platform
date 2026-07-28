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
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_access import (
    ResearchKnowledgeConfidenceAccess,
)
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_registry import (
    ResearchKnowledgeConfidenceRegistry,
)
from quant_platform.research.knowledge.consumption.knowledge_consumption_access import (
    KnowledgeConsumptionAccess,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_access import (
    ResearchKnowledgeEvolutionAccess,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_registry import (
    ResearchKnowledgeEvolutionRegistry,
)
from quant_platform.research.knowledge.evolution.research_knowledge_evolution_service import (
    ResearchKnowledgeEvolutionService,
)
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
from quant_platform.research.knowledge.version.knowledge_version_access import (
    KnowledgeVersionAccess,
)


def build_evolution_environment() -> tuple[
    ResearchValidatedKnowledgeRegistry,
    ResearchKnowledgeEvolutionRegistry,
    ResearchKnowledgeEvolutionService,
    ResearchKnowledgeEvolutionAccess,
]:
    datasets = DatasetRegistry()
    report = MarketDataQualityChecker().check(
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
    datasets.register("dataset-evolution", "AAPL", "v1", "synthetic", report)
    access = DatasetAccess(datasets)
    researches = ResearchRegistry(access)
    configurations = ResearchConfigurationRegistry(researches)
    executions = ResearchExecutionRegistry(configurations, researches, access)
    results = ResearchResultRegistry(executions)

    for number in (1, 2, 3):
        research_id = f"research-evolution-{number}"
        configuration_id = f"cfg-evolution-{number}"
        execution_id = f"exec-evolution-{number}"
        researches.register(
            research_id, "Evolution", "Test evolution", "dataset-evolution", "v1"
        )
        configurations.register(configuration_id, research_id, "read-only", "cfg")
        executions.register(execution_id, configuration_id)
        executions.start(execution_id)
        executions.complete(execution_id)
        results.register(f"result-evolution-{number}", execution_id)

    candidates = ResearchKnowledgeCandidateRegistry(results)
    candidates.register(
        "candidate-evolution",
        "result-evolution-1",
        "Pattern",
        "Original observation",
    )
    validated = ResearchValidatedKnowledgeRegistry(candidates)
    validated.register(
        "knowledge-v1",
        "candidate-evolution",
        "result-evolution-1",
        "Pattern",
        "Original observation",
    )
    candidates.register(
        "candidate-evolution-other",
        "result-evolution-3",
        "Pattern",
        "Independent observation",
    )
    validated.register(
        "knowledge-other",
        "candidate-evolution-other",
        "result-evolution-3",
        "Pattern",
        "Independent observation",
    )
    evolution = ResearchKnowledgeEvolutionRegistry(validated, results)
    return (
        validated,
        evolution,
        ResearchKnowledgeEvolutionService(evolution),
        ResearchKnowledgeEvolutionAccess(evolution),
    )


def test_evolve_creates_an_immutable_linear_version_with_full_traceability():
    validated, evolution, service, access = build_evolution_environment()
    original = validated.get("knowledge-v1")

    version = service.evolve(
        evolution_id="knowledge-v2",
        previous_knowledge_id="knowledge-v1",
        evidence_result_id="result-evolution-2",
        description="Observation updated by new evidence",
    )

    assert version.evolution_id == "knowledge-v2"
    assert version.previous_knowledge_id == "knowledge-v1"
    assert version.candidate_id == "candidate-evolution"
    assert version.result_id == "result-evolution-1"
    assert version.evidence_result_id == "result-evolution-2"
    assert version.version == "2"
    assert version.status == "VALIDATED"
    assert access.get("knowledge-v2") == version
    assert evolution.get_predecessor("knowledge-v2") == original
    assert original is not None
    assert original.description == "Original observation"


def test_evolve_rejects_unknown_or_invalid_predecessor_and_unknown_evidence():
    validated, _, service, _ = build_evolution_environment()

    with pytest.raises(ValueError, match="unknown validated knowledge"):
        service.evolve("knowledge-v2", "missing", "result-evolution-2", "Updated")

    knowledge = validated.get("knowledge-v1")
    assert knowledge is not None
    knowledge.status = "INVALID"
    with pytest.raises(ValueError, match="not in VALIDATED state"):
        service.evolve("knowledge-v2", "knowledge-v1", "result-evolution-2", "Updated")

    knowledge.status = "VALIDATED"
    with pytest.raises(ValueError, match="unknown evidence result"):
        service.evolve("knowledge-v2", "knowledge-v1", "missing-result", "Updated")


def test_evolve_rejects_multiple_successors_and_identifier_cycles():
    _, _, service, _ = build_evolution_environment()
    service.evolve("knowledge-v2", "knowledge-v1", "result-evolution-2", "Updated")

    with pytest.raises(ValueError, match="already has an evolved version"):
        service.evolve(
            "knowledge-v3", "knowledge-v1", "result-evolution-2", "Parallel update"
        )

    with pytest.raises(ValueError, match="already registered"):
        service.evolve("knowledge-v1", "knowledge-v2", "result-evolution-2", "Cycle")


def test_versions_are_compatible_with_confidence_relationship_and_consumption():
    validated, evolution, service, evolution_access = build_evolution_environment()
    versions = KnowledgeVersionAccess(
        ResearchValidatedKnowledgeAccess(validated), evolution_access
    )
    confidence_registry = ResearchKnowledgeConfidenceRegistry(versions)
    relationship_registry = ResearchKnowledgeRelationshipRegistry(versions)
    consumption = KnowledgeConsumptionAccess(
        versions,
        ResearchKnowledgeConfidenceAccess(confidence_registry),
        ResearchKnowledgeRelationshipAccess(relationship_registry),
    )
    candidate = validated._candidate_registry.get("candidate-evolution")
    original = validated.get("knowledge-v1")
    original_confidence = confidence_registry.register(
        "confidence-v1", "knowledge-v1", "high"
    )
    original_relationship = relationship_registry.register(
        "relationship-v1-other", "knowledge-v1", "knowledge-other", "supports"
    )
    original_public_view = consumption.get("knowledge-v1")

    evolved = service.evolve(
        "knowledge-v2",
        "knowledge-v1",
        "result-evolution-2",
        "Observation updated by new evidence",
    )
    assert consumption.get("knowledge-v1") == original_public_view
    evolved_confidence = confidence_registry.register(
        "confidence-v2", "knowledge-v2", "low"
    )
    relationship = relationship_registry.register(
        "relationship-v2-v1", "knowledge-v2", "knowledge-v1", "refines"
    )

    assert candidate is not None
    assert candidate.description == "Original observation"
    assert original is not None
    assert original.description == "Original observation"
    assert confidence_registry.get("confidence-v1") == original_confidence
    assert relationship_registry.list() == [original_relationship, relationship]
    assert evolved_confidence.validated_knowledge_id == evolved.evolution_id
    public_version = consumption.get("knowledge-v2")
    assert public_version.knowledge_id == "knowledge-v2"
    assert public_version.confidence_reference == "confidence-v2"
    assert public_version.relationship_references == ("relationship-v2-v1",)


def test_evolution_record_has_only_the_contractual_data_fields():
    from quant_platform.research.knowledge.evolution.research_knowledge_evolution_record import (
        ResearchKnowledgeEvolutionRecord,
    )

    assert tuple(ResearchKnowledgeEvolutionRecord.__dataclass_fields__) == (
        "evolution_id",
        "previous_knowledge_id",
        "candidate_id",
        "result_id",
        "evidence_result_id",
        "knowledge_type",
        "description",
        "version",
        "created_at",
        "status",
    )


def test_downstream_modules_depend_on_the_knowledge_version_contract():
    from pathlib import Path

    files = (
        "confidence/research_knowledge_confidence_registry.py",
        "relationship/research_knowledge_relationship_registry.py",
        "consumption/knowledge_consumption_access.py",
    )
    root = Path("src/quant_platform/research/knowledge")
    for relative_path in files:
        source = (root / relative_path).read_text(encoding="utf-8")
        assert "knowledge.version.knowledge_version" in source
        assert "validation.research_validated_knowledge" not in source
