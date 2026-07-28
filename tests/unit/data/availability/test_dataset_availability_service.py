from datetime import datetime
from pathlib import Path

import pytest

from quant_platform.data.access import DatasetAccess
from quant_platform.data.availability import (
    AvailableDataset,
    DatasetAvailabilityAccess,
    DatasetAvailabilityRegistry,
    DatasetAvailabilityService,
    DatasetContentReference,
    DatasetContentStore,
)
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry
from quant_platform.research import ResearchDatasetConsumer


def market_data() -> list[MarketData]:
    return [
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


def availability_stack() -> tuple[
    DatasetRegistry,
    DatasetContentStore,
    DatasetAvailabilityRegistry,
    DatasetAvailabilityService,
]:
    datasets = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check(market_data())
    for version in ("v1", "v2"):
        datasets.register(
            dataset_id="dataset-A",
            name="AAPL sample",
            version=version,
            source="synthetic",
            quality_report=quality_report,
        )
    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    service = DatasetAvailabilityService(
        DatasetAccess(datasets), store, availability_registry
    )
    return datasets, store, availability_registry, service


def test_publish_creates_available_dataset_for_explicit_version() -> None:
    datasets, store, availability_registry, service = availability_stack()
    before = datasets.get("dataset-A", "v1")
    source_data = market_data()

    available = service.publish("dataset-A", "v1", source_data)

    assert isinstance(available, AvailableDataset)
    assert available.dataset_id == "dataset-A"
    assert available.version == "v1"
    assert available.quality_reference == "market_data"
    assert available.coverage.record_count == 1
    assert availability_registry.get("dataset-A", "v1").status == "AVAILABLE"  # type: ignore[union-attr]
    assert service.resolve(available.content_reference) == tuple(source_data)
    assert store.resolve(available.content_reference) == tuple(source_data)
    assert datasets.get("dataset-A", "v1") == before


def test_versions_coexist_and_public_access_requires_exact_version() -> None:
    _, store, availability_registry, service = availability_stack()
    first = service.publish("dataset-A", "v1", market_data())
    second = service.publish("dataset-A", "v2", market_data())
    access = DatasetAvailabilityAccess(availability_registry, store)

    assert access.get("dataset-A", "v1") == first
    assert access.get("dataset-A", "v2") == second
    assert access.exists("dataset-A", "v1")
    assert not access.exists("dataset-A", "v3")
    assert access.list() == (first, second)
    with pytest.raises(TypeError):
        access.get("dataset-A")  # type: ignore[call-arg]


def test_rejects_content_reference_owned_by_another_dataset_or_version() -> None:
    datasets, store, availability_registry, service = availability_stack()
    quality_report = MarketDataQualityChecker().check(market_data())
    datasets.register(
        dataset_id="dataset-B",
        name="Other sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    foreign_reference = DatasetContentReference("dataset-B", "v1", "content-B")
    store.register_content(foreign_reference, market_data())

    with pytest.raises(ValueError, match="dataset_id/version"):
        service.publish("dataset-A", "v1", foreign_reference)
    with pytest.raises(ValueError, match="dataset_id/version"):
        service.publish(
            "dataset-A",
            "v2",
            DatasetContentReference("dataset-A", "v1", "content-B"),
        )
    assert not availability_registry.exists("dataset-A", "v1")


def test_research_consumer_resolves_only_public_available_content() -> None:
    _, store, availability_registry, service = availability_stack()
    expected = service.publish("dataset-A", "v1", market_data())
    research = ResearchDatasetConsumer(
        DatasetAvailabilityAccess(availability_registry, store)
    )

    assert research.load("dataset-A", "v1") == expected
    assert research.load_content("dataset-A", "v1") == tuple(market_data())
    assert research.load("dataset-A", "v2") is None


def test_research_does_not_import_data_internals() -> None:
    forbidden = (
        "DatasetRegistry",
        "DatasetAccess",
        "DatasetContentStore",
        "DatasetAvailabilityRegistry",
        "DatasetRecord",
    )
    research_sources = Path("src/quant_platform/research").rglob("*.py")
    source = "\n".join(path.read_text(encoding="utf-8") for path in research_sources)

    for name in forbidden:
        assert name not in source
