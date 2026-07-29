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
from quant_platform.research.knowledge.validation.research_knowledge_validation_service import (
    ResearchKnowledgeValidationService,
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
        dataset_id="dataset-validation",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def build_candidate_environment() -> (
    tuple[ResearchKnowledgeCandidateRegistry, ResearchKnowledgeValidationService]
):
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research_registry.register(
        research_id="research-validation",
        name="Validation test",
        objective="Test validation workflow",
        dataset_id="dataset-validation",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-validation",
        research_id="research-validation",
        access_policy="read-only",
        description="cfg",
    )
    exec_registry.register(
        execution_id="exec-validation", configuration_id="cfg-validation"
    )
    exec_registry.start("exec-validation")
    exec_registry.complete("exec-validation")
    result_registry.register(result_id="res-validation", execution_id="exec-validation")

    candidate_registry = ResearchKnowledgeCandidateRegistry(result_registry)
    candidate_registry.register(
        knowledge_candidate_id="candidate-validation",
        result_id="res-validation",
        knowledge_type="Pattern",
        description="A reusable observation",
    )

    service = ResearchKnowledgeValidationService(candidate_registry)
    return candidate_registry, service


def test_validate_creates_validated_knowledge_and_preserves_candidate():
    candidate_registry, service = build_candidate_environment()

    candidate = candidate_registry.get("candidate-validation")
    assert candidate is not None

    validated = service.validate(
        candidate_id="candidate-validation",
        knowledge_id="K-validation",
        knowledge_version_id="KV-validation-001",
    )

    assert validated.knowledge_id == "K-validation"
    assert validated.knowledge_version_id == "KV-validation-001"
    assert validated.knowledge_id != validated.knowledge_version_id
    assert validated.version == "1"
    assert validated.candidate_id == "candidate-validation"
    assert validated.result_id == "res-validation"
    assert validated.status == "VALIDATED"
    assert validated.created_at is not None

    preserved = candidate_registry.get("candidate-validation")
    assert preserved is not None
    assert preserved.status == "CANDIDATE"
    assert preserved.description == "A reusable observation"


def test_validate_unknown_candidate_raises():
    _, service = build_candidate_environment()

    with pytest.raises(ValueError, match="unknown candidate"):
        service.validate(
            candidate_id="missing-candidate",
            knowledge_id="K-missing",
            knowledge_version_id="KV-missing-001",
        )


def test_validate_candidate_twice_raises():
    _, service = build_candidate_environment()

    service.validate(
        candidate_id="candidate-validation",
        knowledge_id="K-validation",
        knowledge_version_id="KV-validation-001",
    )

    with pytest.raises(ValueError, match="already validated"):
        service.validate(
            candidate_id="candidate-validation",
            knowledge_id="K-validation",
            knowledge_version_id="KV-validation-002",
        )


def test_registry_rejects_reused_knowledge_version_id() -> None:
    _, service = build_candidate_environment()
    service.validate("candidate-validation", "K-validation", "KV-validation-001")

    with pytest.raises(ValueError, match="knowledge version already registered"):
        service._validated_registry.register(  # type: ignore[attr-defined]
            knowledge_id="K-other",
            knowledge_version_id="KV-validation-001",
            candidate_id="candidate-validation",
            result_id="res-validation",
            knowledge_type="Pattern",
            description="Duplicate version identity",
        )
