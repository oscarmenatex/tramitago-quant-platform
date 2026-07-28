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
    CREATED,
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
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    return registry


def test_register_and_retrieve_result():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research_registry.register(
        research_id="research-001",
        name="Result test",
        objective="Test result",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    config_registry.register(
        configuration_id="cfg-001",
        research_id="research-001",
        access_policy="read-only",
        description="cfg",
    )

    exec_registry.register(execution_id="exec-001", configuration_id="cfg-001")
    exec_registry.start("exec-001")
    exec_registry.complete("exec-001")

    record = result_registry.register(result_id="res-001", execution_id="exec-001")
    assert record.result_id == "res-001"
    assert record.execution_id == "exec-001"
    assert record.status == CREATED
    assert record.created_at is not None

    fetched = result_registry.get("res-001")
    assert fetched is not None
    assert fetched.result_id == "res-001"


def test_register_unknown_execution_raises():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    try:
        result_registry.register(result_id="res-002", execution_id="missing-exec")
        assert False, "Expected ValueError for unknown execution"
    except ValueError as exc:
        assert "unknown execution" in str(exc)


def test_result_id_mandatory():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research_registry.register(
        research_id="research-002",
        name="Result test 2",
        objective="Test result 2",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    config_registry.register(
        configuration_id="cfg-002",
        research_id="research-002",
        access_policy="read-only",
        description="cfg2",
    )

    exec_registry.register(execution_id="exec-002", configuration_id="cfg-002")
    exec_registry.start("exec-002")
    exec_registry.complete("exec-002")

    try:
        result_registry.register(result_id="", execution_id="exec-002")
        assert False, "Expected ValueError for missing result_id"
    except ValueError as exc:
        assert "result_id is required" in str(exc)


def test_one_result_per_execution():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research_registry.register(
        research_id="research-003",
        name="Result test 3",
        objective="Test result 3",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    config_registry.register(
        configuration_id="cfg-003",
        research_id="research-003",
        access_policy="read-only",
        description="cfg3",
    )

    exec_registry.register(execution_id="exec-003", configuration_id="cfg-003")
    exec_registry.start("exec-003")
    exec_registry.complete("exec-003")

    result_registry.register(result_id="res-003", execution_id="exec-003")

    try:
        result_registry.register(result_id="res-004", execution_id="exec-003")
        assert False, "Expected ValueError for duplicate result on execution"
    except ValueError as exc:
        assert "result already registered for execution" in str(exc)
