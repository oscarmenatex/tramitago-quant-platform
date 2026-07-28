from datetime import datetime

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
        validated_knowledge_id="validated-validation",
    )

    assert validated.validated_knowledge_id == "validated-validation"
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

    try:
        service.validate(
            candidate_id="missing-candidate", validated_knowledge_id="validated-2"
        )
        assert False, "Expected ValueError for unknown candidate"
    except ValueError as exc:
        assert "unknown candidate" in str(exc)


def test_validate_candidate_twice_raises():
    _, service = build_candidate_environment()

    service.validate(
        candidate_id="candidate-validation", validated_knowledge_id="validated-3"
    )

    try:
        service.validate(
            candidate_id="candidate-validation", validated_knowledge_id="validated-4"
        )
        assert False, "Expected ValueError for duplicate validation"
    except ValueError as exc:
        assert "already validated" in str(exc)
