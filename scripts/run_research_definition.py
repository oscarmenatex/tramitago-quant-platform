"""Research Definition MVP demonstration."""

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
from quant_platform.research import ResearchRegistry


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
    quality_report = MarketDataQualityChecker().check(build_valid_market_data())

    registry.register(
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(registry), store, availability_registry
    ).publish("dataset-001", "v1", build_valid_market_data())
    research_registry = ResearchRegistry(
        DatasetAvailabilityAccess(availability_registry, store)
    )

    research = research_registry.register(
        research_id="research-001",
        name="First research definition",
        objective="Define a first research using the available dataset",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    print(f"research_id: {research.research_id}")
    print(f"name: {research.name}")
    print(f"objective: {research.objective}")
    print(f"dataset_id: {research.dataset_id}")
    print(f"dataset_version: {research.dataset_version}")
    print(f"status: {research.status}")


if __name__ == "__main__":
    main()
