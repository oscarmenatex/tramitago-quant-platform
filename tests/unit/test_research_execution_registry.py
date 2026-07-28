from datetime import datetime

from quant_platform.data.access import DatasetAccess
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry
from quant_platform.research import ResearchRegistry
from quant_platform.research.configuration import ResearchConfigurationRegistry
from quant_platform.research.execution.research_execution_registry import (
    ResearchExecutionRegistry,
    CREATED,
    RUNNING,
    COMPLETED,
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


def test_register_and_execute_lifecycle():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )

    research_registry.register(
        research_id="research-001",
        name="Exec test",
        objective="Test execution",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    config_registry.register(
        configuration_id="cfg-001",
        research_id="research-001",
        access_policy="read-only",
        description="cfg",
    )

    record = exec_registry.register(execution_id="exec-001", configuration_id="cfg-001")
    assert record.execution_id == "exec-001"
    assert record.status == CREATED
    assert record.research_id == "research-001"
    assert record.dataset_id == "dataset-001"

    # start
    started = exec_registry.start("exec-001")
    assert started.status == RUNNING
    assert started.started_at is not None

    # complete
    completed = exec_registry.complete("exec-001")
    assert completed.status == COMPLETED
    assert completed.finished_at is not None


def test_register_unknown_configuration_raises():
    registry = build_available_dataset()
    access = DatasetAccess(registry)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )

    try:
        exec_registry.register(execution_id="exec-002", configuration_id="missing-cfg")
        assert False, "Expected ValueError for unknown configuration"
    except ValueError as exc:
        assert "unknown configuration" in str(exc)
