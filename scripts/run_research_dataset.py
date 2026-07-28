"""Research dataset consumption MVP demonstration."""

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


def build_valid_market_data() -> list[MarketData]:
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


def main() -> None:
    registry = DatasetRegistry()
    checker = MarketDataQualityChecker()
    quality_report = checker.check(build_valid_market_data())

    registry.register(
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    availability_registry = DatasetAvailabilityRegistry()
    store = DatasetContentStore()
    availability_service = DatasetAvailabilityService(
        DatasetAccess(registry), store, availability_registry
    )
    availability_service.publish("dataset-001", "v1", build_valid_market_data())

    consumer = ResearchDatasetConsumer(
        DatasetAvailabilityAccess(availability_registry, store)
    )
    available = consumer.load("dataset-001", "v1")

    if available is None:
        print("Available dataset not found")
        return

    print(f"dataset_id: {available.dataset_id}")
    print(f"version: {available.version}")
    print(f"quality_reference: {available.quality_reference}")
    print(f"content_reference: {available.content_reference.content_id}")
    print(f"coverage records: {available.coverage.record_count}")


if __name__ == "__main__":
    main()
