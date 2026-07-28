"""Demo: Research Result MVP

Shows Execution -> Result -> Query flow without performing calculations.
"""

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
from quant_platform.research.execution.research_execution_registry import (
    ResearchExecutionRegistry,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)


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

    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(registry), store, availability_registry
    ).publish("dataset-001", "v1", build_valid_market_data())
    access = DatasetAvailabilityAccess(availability_registry, store)
    research_registry = ResearchRegistry(access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    exec_registry = ResearchExecutionRegistry(
        config_registry, research_registry, access
    )
    result_registry = ResearchResultRegistry(exec_registry)

    research = research_registry.register(
        research_id="research-001",
        name="Result demo",
        objective="Demo result",
        dataset_id="dataset-001",
        dataset_version="v1",
    )

    config = config_registry.register(
        configuration_id="cfg-001",
        research_id=research.research_id,
        access_policy="read-only",
        description="Demo config",
    )

    execution = exec_registry.register(
        execution_id="exec-001", configuration_id=config.configuration_id
    )
    print("execution created:", execution)

    exec_registry.start("exec-001")
    print("execution running:", exec_registry.get("exec-001"))

    exec_registry.complete("exec-001")
    print("execution completed:", exec_registry.get("exec-001"))

    result = result_registry.register(result_id="res-001", execution_id="exec-001")
    print("result created:", result)

    fetched = result_registry.get("res-001")
    print("fetched result:", fetched)


if __name__ == "__main__":
    main()
