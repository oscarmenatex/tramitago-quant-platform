"""Research Configuration MVP demonstration."""

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
from quant_platform.research.configuration import ResearchConfigurationRegistry


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
    config_registry = ResearchConfigurationRegistry(research_registry)

    research = research_registry.register(
        research_id="research-001",
        name="AAPL research definition",
        objective="Define dataset usage for AAPL research",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    configuration = config_registry.register(
        configuration_id="config-001",
        research_id=research.research_id,
        access_policy="read-only",
        description="Use AAPL dataset with read-only access for research evaluation",
    )

    print(f"research_id: {research.research_id}")
    print(f"configuration_id: {configuration.configuration_id}")
    # dataset_id is owned by the ResearchRecord
    print(f"dataset_id: {research_registry.get(research.research_id).dataset_id}")
    print(f"access_policy: {configuration.access_policy}")
    print(f"description: {configuration.description}")


if __name__ == "__main__":
    main()
