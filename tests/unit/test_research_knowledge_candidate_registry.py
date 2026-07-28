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
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_access import (
    ResearchKnowledgeCandidateAccess,
)
from quant_platform.research.knowledge.candidate.research_knowledge_candidate_registry import (
    ResearchKnowledgeCandidateRegistry,
    CANDIDATE,
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
        dataset_id="dataset-candidate",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def build_research_chain() -> tuple[
    ResearchResultRegistry,
    ResearchKnowledgeCandidateRegistry,
    ResearchKnowledgeCandidateAccess,
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
        research_id="research-candidate",
        name="Candidate test",
        objective="Test candidate registration",
        dataset_id="dataset-candidate",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-candidate",
        research_id="research-candidate",
        access_policy="read-only",
        description="cfg",
    )
    exec_registry.register(
        execution_id="exec-candidate", configuration_id="cfg-candidate"
    )
    exec_registry.start("exec-candidate")
    exec_registry.complete("exec-candidate")
    result_registry.register(result_id="res-candidate", execution_id="exec-candidate")

    candidate_registry = ResearchKnowledgeCandidateRegistry(result_registry)
    access_layer = ResearchKnowledgeCandidateAccess(candidate_registry)
    return result_registry, candidate_registry, access_layer


def test_register_and_retrieve_candidate():
    _, candidate_registry, candidate_access = build_research_chain()

    record = candidate_registry.register(
        knowledge_candidate_id="candidate-001",
        result_id="res-candidate",
        knowledge_type="Pattern",
        description="A reusable observation from a research result",
    )

    assert record.knowledge_candidate_id == "candidate-001"
    assert record.result_id == "res-candidate"
    assert record.knowledge_type == "Pattern"
    assert record.description == "A reusable observation from a research result"
    assert record.status == CANDIDATE
    assert record.created_at is not None
    assert record.version == "1"

    fetched = candidate_access.get("candidate-001")
    assert fetched is not None
    assert fetched.knowledge_candidate_id == "candidate-001"
    assert candidate_access.exists("candidate-001") is True
    assert candidate_access.exists("candidate-999") is False
    assert len(candidate_access.list()) == 1


def test_register_unknown_result_raises():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)
    candidate_registry = ResearchKnowledgeCandidateRegistry(result_registry)

    try:
        candidate_registry.register(
            knowledge_candidate_id="candidate-002",
            result_id="missing-result",
            knowledge_type="Pattern",
            description="Should fail",
        )
        assert False, "Expected ValueError for unknown result"
    except ValueError as exc:
        assert "unknown result" in str(exc)


def test_empty_required_fields_raise():
    _, candidate_registry, _ = build_research_chain()

    for kwargs in [
        {
            "knowledge_candidate_id": "",
            "result_id": "res-candidate",
            "knowledge_type": "Pattern",
            "description": "desc",
        },
        {
            "knowledge_candidate_id": "candidate-003",
            "result_id": "",
            "knowledge_type": "Pattern",
            "description": "desc",
        },
        {
            "knowledge_candidate_id": "candidate-003",
            "result_id": "res-candidate",
            "knowledge_type": "",
            "description": "desc",
        },
        {
            "knowledge_candidate_id": "candidate-003",
            "result_id": "res-candidate",
            "knowledge_type": "Pattern",
            "description": "",
        },
    ]:
        try:
            candidate_registry.register(**kwargs)
            assert False, f"Expected ValueError for invalid input {kwargs}"
        except ValueError:
            pass


def test_duplicate_candidate_id_raises():
    _, candidate_registry, _ = build_research_chain()

    candidate_registry.register(
        knowledge_candidate_id="candidate-004",
        result_id="res-candidate",
        knowledge_type="Pattern",
        description="First candidate",
    )

    try:
        candidate_registry.register(
            knowledge_candidate_id="candidate-004",
            result_id="res-candidate-2",
            knowledge_type="Pattern",
            description="Second candidate",
        )
        assert False, "Expected ValueError for duplicate candidate id"
    except ValueError as exc:
        assert "already registered" in str(exc)


def test_one_candidate_per_result_raises():
    _, candidate_registry, _ = build_research_chain()

    candidate_registry.register(
        knowledge_candidate_id="candidate-005",
        result_id="res-candidate",
        knowledge_type="Pattern",
        description="First candidate",
    )

    try:
        candidate_registry.register(
            knowledge_candidate_id="candidate-006",
            result_id="res-candidate",
            knowledge_type="Pattern",
            description="Second candidate",
        )
        assert False, "Expected ValueError for duplicate candidate per result"
    except ValueError as exc:
        assert "already registered for result" in str(exc)


def test_list_returns_registered_candidates():
    _, candidate_registry, _ = build_research_chain()

    candidate_registry.register(
        knowledge_candidate_id="candidate-007",
        result_id="res-candidate",
        knowledge_type="Pattern",
        description="Listed candidate",
    )

    records = candidate_registry.list()
    assert len(records) == 1
    assert records[0].knowledge_candidate_id == "candidate-007"


def test_candidate_boundary_remains_distinct_from_knowledge_model():
    _, candidate_registry, _ = build_research_chain()

    record = candidate_registry.register(
        knowledge_candidate_id="candidate-boundary",
        result_id="res-candidate",
        knowledge_type="Pattern",
        description="Conceptual boundary check",
    )

    assert record.knowledge_candidate_id == "candidate-boundary"
    assert record.status == CANDIDATE
    assert not hasattr(record, "knowledge_id")
    assert hasattr(record, "knowledge_candidate_id")
