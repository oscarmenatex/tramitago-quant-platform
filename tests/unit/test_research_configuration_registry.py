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
from quant_platform.research.research_registry import ResearchRegistry
from quant_platform.research.configuration.research_configuration_registry import (
    ResearchConfigurationRegistry,
)


def test_research_configuration_registry_register_and_get():
    dataset_registry = DatasetRegistry()
    content = [
        MarketData(
            "AAPL",
            __import__("datetime").datetime(2024, 1, 2),
            100,
            105,
            99,
            104,
            1_000_000,
        )
    ]
    report = MarketDataQualityChecker().check(content)
    dataset_registry.register("ds-001", "Market Data", "v1", "Yahoo", report)
    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(dataset_registry), store, availability_registry
    ).publish("ds-001", "v1", content)
    research_registry = ResearchRegistry(
        DatasetAvailabilityAccess(availability_registry, store)
    )
    configuration_registry = ResearchConfigurationRegistry(research_registry)

    # register a research definition which links to the dataset
    research_registry.register(
        research_id="research-001",
        name="Market Study",
        objective="Test",
        dataset_id="ds-001",
        dataset_version="v1",
    )

    configuration_record = configuration_registry.register(
        configuration_id="cfg-001",
        research_id="research-001",
        access_policy="read-only",
        description="Minimal research configuration",
    )

    assert configuration_record.configuration_id == "cfg-001"
    assert configuration_record.research_id == "research-001"
    assert configuration_record.access_policy == "read-only"
    assert configuration_record.description == "Minimal research configuration"
    assert configuration_registry.get("cfg-001") == configuration_record
    # dataset_id remains owned by ResearchRecord
    assert (
        research_registry.get(configuration_record.research_id).dataset_id == "ds-001"
    )


def test_research_configuration_registry_register_unknown_dataset_raises():
    dataset_registry = DatasetRegistry()
    dataset_access = DatasetAccess(dataset_registry)
    research_registry = ResearchRegistry(dataset_access)
    configuration_registry = ResearchConfigurationRegistry(research_registry)

    try:
        configuration_registry.register(
            configuration_id="cfg-002",
            research_id="unknown-research",
            access_policy="read-only",
        )
        assert False, "Expected ValueError for unknown research"
    except ValueError as exc:
        assert "unknown research" in str(exc)
