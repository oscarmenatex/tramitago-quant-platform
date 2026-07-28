from datetime import datetime

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
from quant_platform.research import ResearchDatasetConsumer


def consumer() -> ResearchDatasetConsumer:
    content = [MarketData("AAPL", datetime(2024, 1, 2), 100, 105, 99, 104, 1_000_000)]
    datasets = DatasetRegistry()
    report = MarketDataQualityChecker().check(content)
    datasets.register("dataset-001", "AAPL", "v1", "synthetic", report)
    store = DatasetContentStore()
    registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(DatasetAccess(datasets), store, registry).publish(
        "dataset-001", "v1", content
    )
    return ResearchDatasetConsumer(DatasetAvailabilityAccess(registry, store))


def test_research_consumer_loads_contract_and_resolvable_content() -> None:
    value = consumer()

    available = value.load("dataset-001", "v1")

    assert available is not None
    assert available.dataset_id == "dataset-001"
    assert available.version == "v1"
    assert available.quality_reference == "market_data"
    assert value.load_content("dataset-001", "v1") is not None


def test_research_consumer_rejects_missing_version() -> None:
    assert consumer().load("dataset-001", "v2") is None
