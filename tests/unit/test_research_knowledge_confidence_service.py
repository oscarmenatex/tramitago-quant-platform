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
from quant_platform.research.knowledge.confidence.research_knowledge_confidence_service import (
    ResearchKnowledgeConfidenceService,
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
        dataset_id="dataset-confidence",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def build_confidence_environment() -> tuple[
    ResearchKnowledgeConfidenceRegistry,
    ResearchKnowledgeConfidenceService,
    ResearchKnowledgeConfidenceAccess,
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
        research_id="research-confidence",
        name="Confidence test",
        objective="Test confidence workflow",
        dataset_id="dataset-confidence",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-confidence",
        research_id="research-confidence",
        access_policy="read-only",
        description="cfg",
    )
    exec_registry.register(
        execution_id="exec-confidence", configuration_id="cfg-confidence"
    )
    exec_registry.start("exec-confidence")
    exec_registry.complete("exec-confidence")
    result_registry.register(result_id="res-confidence", execution_id="exec-confidence")

    candidate_registry = ResearchKnowledgeCandidateRegistry(result_registry)
    candidate_registry.register(
        knowledge_candidate_id="candidate-confidence",
        result_id="res-confidence",
        knowledge_type="Pattern",
        description="A reusable observation",
    )

    validated_registry = ResearchValidatedKnowledgeRegistry(candidate_registry)
    validated_registry.register(
        validated_knowledge_id="validated-confidence",
        candidate_id="candidate-confidence",
        result_id="res-confidence",
        knowledge_type="Pattern",
        description="A reusable observation",
    )

    confidence_registry = ResearchKnowledgeConfidenceRegistry(validated_registry)
    service = ResearchKnowledgeConfidenceService(confidence_registry)
    access_layer = ResearchKnowledgeConfidenceAccess(confidence_registry)
    return confidence_registry, service, access_layer


def test_assess_creates_confidence_and_preserves_validated_knowledge():
    _, service, _ = build_confidence_environment()

    confidence = service.assess(
        knowledge_confidence_id="confidence-1",
        validated_knowledge_id="validated-confidence",
        confidence_level="high",
    )

    assert confidence.knowledge_confidence_id == "confidence-1"
    assert confidence.validated_knowledge_id == "validated-confidence"
    assert confidence.confidence_level == "HIGH"
    assert confidence.status == "ASSESSED"
    assert confidence.created_at is not None


def test_assess_unknown_validated_knowledge_raises():
    _, service, _ = build_confidence_environment()

    with pytest.raises(ValueError, match="unknown validated knowledge"):
        service.assess(
            knowledge_confidence_id="confidence-2",
            validated_knowledge_id="missing-validated",
            confidence_level="medium",
        )


def test_assess_candidate_id_is_not_a_knowledge_version():
    _, service, _ = build_confidence_environment()

    with pytest.raises(ValueError, match="unknown validated knowledge"):
        service.assess(
            knowledge_confidence_id="confidence-2",
            validated_knowledge_id="candidate-confidence",
            confidence_level="high",
        )


@pytest.mark.parametrize(
    ("knowledge_confidence_id", "validated_knowledge_id", "confidence_level"),
    [
        ("", "validated-confidence", "high"),
        ("confidence-3", "", "high"),
        ("confidence-3", "validated-confidence", ""),
        ("confidence-3", "validated-confidence", "uncertain"),
    ],
)
def test_assess_rejects_empty_or_invalid_inputs(
    knowledge_confidence_id: str,
    validated_knowledge_id: str,
    confidence_level: str,
) -> None:
    _, service, _ = build_confidence_environment()

    with pytest.raises(ValueError):
        service.assess(
            knowledge_confidence_id=knowledge_confidence_id,
            validated_knowledge_id=validated_knowledge_id,
            confidence_level=confidence_level,
        )


def test_assess_duplicate_confidence_id_raises():
    _, service, _ = build_confidence_environment()

    service.assess(
        knowledge_confidence_id="confidence-4",
        validated_knowledge_id="validated-confidence",
        confidence_level="low",
    )

    with pytest.raises(ValueError, match="already registered"):
        service.assess(
            knowledge_confidence_id="confidence-4",
            validated_knowledge_id="validated-confidence",
            confidence_level="high",
        )


def test_assess_duplicate_validated_knowledge_raises():
    _, service, _ = build_confidence_environment()

    service.assess(
        knowledge_confidence_id="confidence-5",
        validated_knowledge_id="validated-confidence",
        confidence_level="medium",
    )

    with pytest.raises(ValueError, match="already registered for validated knowledge"):
        service.assess(
            knowledge_confidence_id="confidence-6",
            validated_knowledge_id="validated-confidence",
            confidence_level="high",
        )


def test_registry_access_and_traceability_preserve_state():
    registry, _, access = build_confidence_environment()

    confidence = registry.register(
        knowledge_confidence_id="confidence-7",
        validated_knowledge_id="validated-confidence",
        confidence_level="high",
    )

    assert registry.exists("confidence-7") is True
    assert access.exists("confidence-7") is True
    assert access.get("confidence-7") == confidence
    assert len(access.list()) == 1
    assert registry.list()[0].validated_knowledge_id == "validated-confidence"
