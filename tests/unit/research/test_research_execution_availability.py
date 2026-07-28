from datetime import datetime

import pytest

from quant_platform.data.access import DatasetAccess
from quant_platform.data.availability import (
    DatasetAvailabilityAccess,
    DatasetAvailabilityRegistry,
    DatasetAvailabilityService,
    DatasetContentStore,
)
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry
from quant_platform.research import ResearchRegistry
from quant_platform.research.configuration import ResearchConfigurationRegistry
from quant_platform.research.execution import ResearchExecutionRegistry


def execution_stack() -> (
    tuple[ResearchRegistry, ResearchConfigurationRegistry, ResearchExecutionRegistry]
):
    content = [MarketData("AAPL", datetime(2024, 1, 2), 100, 105, 99, 104, 1_000_000)]
    datasets = DatasetRegistry()
    report = MarketDataQualityChecker().check(content)
    datasets.register("dataset-001", "AAPL", "v1", "synthetic", report)
    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(datasets), store, availability_registry
    ).publish("dataset-001", "v1", content)
    access = DatasetAvailabilityAccess(availability_registry, store)
    research = ResearchRegistry(access)
    configuration = ResearchConfigurationRegistry(research)
    return (
        research,
        configuration,
        ResearchExecutionRegistry(configuration, research, access),
    )


def test_execution_rechecks_the_exact_available_dataset_version() -> None:
    research, configurations, executions = execution_stack()
    research.register("research-001", "Exact version", "test", "dataset-001", "v1")
    configurations.register("config-001", "research-001", "read-only", "test")

    execution = executions.register("execution-001", "config-001")

    assert execution.dataset_id == "dataset-001"
    assert execution.dataset_version == "v1"


def test_definition_rejects_an_unavailable_version() -> None:
    research, _, _ = execution_stack()

    with pytest.raises(ValueError, match="available dataset"):
        research.register("research-002", "Wrong version", "test", "dataset-001", "v2")
