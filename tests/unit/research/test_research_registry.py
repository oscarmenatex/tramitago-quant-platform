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


def available_access() -> DatasetAvailabilityAccess:
    data = [MarketData("AAPL", datetime(2024, 1, 2), 100, 105, 99, 104, 1_000_000)]
    registry = DatasetRegistry()
    report = MarketDataQualityChecker().check(data)
    registry.register("dataset-001", "AAPL", "v1", "synthetic", report)
    registry.register("dataset-001", "AAPL", "v2", "synthetic", report)
    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(registry), store, availability_registry
    ).publish("dataset-001", "v1", data)
    DatasetAvailabilityService(
        DatasetAccess(registry), store, availability_registry
    ).publish("dataset-001", "v2", data)
    return DatasetAvailabilityAccess(availability_registry, store)


def test_register_research_definition_requires_exact_available_dataset() -> None:
    research_registry = ResearchRegistry(available_access())

    research = research_registry.register(
        research_id="research-001",
        name="Mean reversion test",
        objective="Verify mean reversion signal on AAPL",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    assert research.dataset_id == "dataset-001"
    assert research.dataset_version == "v1"
    assert research.status == "DEFINED"


def test_register_research_rejects_unavailable_version() -> None:
    research_registry = ResearchRegistry(available_access())

    with pytest.raises(ValueError, match="available dataset"):
        research_registry.register(
            research_id="research-002",
            name="Invalid version",
            objective="Must not use an implicit version",
            dataset_id="dataset-001",
            dataset_version="v3",
        )


def test_two_research_definitions_can_use_distinct_dataset_versions() -> None:
    research_registry = ResearchRegistry(available_access())

    first = research_registry.register(
        "research-v1", "First", "Use v1", "dataset-001", "v1"
    )
    second = research_registry.register(
        "research-v2", "Second", "Use v2", "dataset-001", "v2"
    )

    assert (first.dataset_id, first.dataset_version) == ("dataset-001", "v1")
    assert (second.dataset_id, second.dataset_version) == ("dataset-001", "v2")


def test_register_requires_a_non_empty_explicit_version() -> None:
    research_registry = ResearchRegistry(available_access())

    with pytest.raises(TypeError):
        research_registry.register(
            research_id="research-missing-version",
            name="Missing version",
            objective="Must be explicit",
            dataset_id="dataset-001",
        )
    with pytest.raises(ValueError, match="non-empty string"):
        research_registry.register(
            research_id="research-empty-version",
            name="Empty version",
            objective="Must not be blank",
            dataset_id="dataset-001",
            dataset_version="   ",
        )
