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
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)
from quant_platform.research.knowledge.research_knowledge_registry import (
    ResearchKnowledgeRegistry,
    CREATED,
)
from quant_platform.research.knowledge.research_knowledge_access import (
    ResearchKnowledgeAccess,
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
        dataset_id="dataset-knowledge",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def build_research_chain() -> (
    tuple[ResearchResultRegistry, ResearchKnowledgeRegistry, ResearchKnowledgeAccess]
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
        research_id="research-knowledge",
        name="Knowledge test",
        objective="Test knowledge registration",
        dataset_id="dataset-knowledge",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-knowledge",
        research_id="research-knowledge",
        access_policy="read-only",
        description="cfg",
    )
    exec_registry.register(
        execution_id="exec-knowledge", configuration_id="cfg-knowledge"
    )
    exec_registry.start("exec-knowledge")
    exec_registry.complete("exec-knowledge")
    result_registry.register(result_id="res-knowledge", execution_id="exec-knowledge")

    knowledge_registry = ResearchKnowledgeRegistry(result_registry)
    access_layer = ResearchKnowledgeAccess(knowledge_registry)
    return result_registry, knowledge_registry, access_layer


def test_register_and_retrieve_knowledge():
    _, knowledge_registry, knowledge_access = build_research_chain()

    record = knowledge_registry.register(
        knowledge_id="knowledge-001",
        result_id="res-knowledge",
        knowledge_type="MVP",
        description="Reusable insight derived from a research result",
    )

    assert record.knowledge_id == "knowledge-001"
    assert record.result_id == "res-knowledge"
    assert record.knowledge_type == "MVP"
    assert record.description == "Reusable insight derived from a research result"
    assert record.status == CREATED
    assert record.created_at is not None
    assert record.version == "v1"

    fetched = knowledge_access.get("knowledge-001")
    assert fetched is not None
    assert fetched.knowledge_id == "knowledge-001"
    assert knowledge_access.exists("knowledge-001") is True
    assert knowledge_access.exists("knowledge-999") is False
    assert len(knowledge_access.list()) == 1


def test_register_unknown_result_raises():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)
    knowledge_registry = ResearchKnowledgeRegistry(result_registry)

    try:
        knowledge_registry.register(
            knowledge_id="knowledge-002",
            result_id="missing-result",
            knowledge_type="MVP",
            description="Should fail",
        )
        assert False, "Expected ValueError for unknown result"
    except ValueError as exc:
        assert "unknown result" in str(exc)


def test_duplicate_knowledge_for_result_raises():
    _, knowledge_registry, _ = build_research_chain()

    knowledge_registry.register(
        knowledge_id="knowledge-003",
        result_id="res-knowledge",
        knowledge_type="MVP",
        description="First knowledge",
    )

    try:
        knowledge_registry.register(
            knowledge_id="knowledge-004",
            result_id="res-knowledge",
            knowledge_type="MVP",
            description="Second knowledge",
        )
        assert False, "Expected ValueError for duplicate knowledge for result"
    except ValueError as exc:
        assert "already registered for result" in str(exc)


def test_registry_exposes_list_of_knowledge_records():
    _, knowledge_registry, _ = build_research_chain()

    knowledge_registry.register(
        knowledge_id="knowledge-005",
        result_id="res-knowledge",
        knowledge_type="MVP",
        description="Listed knowledge",
    )

    records = knowledge_registry.list()
    assert len(records) == 1
    assert records[0].knowledge_id == "knowledge-005"
