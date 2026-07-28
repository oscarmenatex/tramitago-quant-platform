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
from quant_platform.research.knowledge.research_knowledge_access import (
    ResearchKnowledgeAccess,
)
from quant_platform.research.knowledge.research_knowledge_registry import (
    ResearchKnowledgeRegistry,
)
from quant_platform.research.result.research_result_registry import (
    ResearchResultRegistry,
)


def main() -> None:
    dataset_registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check(
        [
            MarketData(
                symbol="AAPL",
                timestamp=datetime(2024, 1, 3),
                open=101.0,
                high=106.0,
                low=100.0,
                close=105.0,
                volume=1_100_000.0,
            )
        ]
    )
    dataset_registry.register(
        dataset_id="dataset-demo",
        name="AAPL demo",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    content = [
        MarketData(
            symbol="AAPL",
            timestamp=datetime(2024, 1, 3),
            open=101.0,
            high=106.0,
            low=100.0,
            close=105.0,
            volume=1_100_000.0,
        )
    ]
    store = DatasetContentStore()
    availability_registry = DatasetAvailabilityRegistry()
    DatasetAvailabilityService(
        DatasetAccess(dataset_registry), store, availability_registry
    ).publish("dataset-demo", "v1", content)
    dataset_access = DatasetAvailabilityAccess(availability_registry, store)
    research_registry = ResearchRegistry(dataset_access)
    config_registry = ResearchConfigurationRegistry(research_registry)
    execution_registry = ResearchExecutionRegistry(
        config_registry,
        research_registry,
        dataset_access,
    )
    result_registry = ResearchResultRegistry(execution_registry)
    knowledge_registry = ResearchKnowledgeRegistry(result_registry)
    knowledge_access = ResearchKnowledgeAccess(knowledge_registry)

    research_registry.register(
        research_id="research-demo",
        name="Knowledge demo",
        objective="Demonstrate knowledge MVP",
        dataset_id="dataset-demo",
        dataset_version="v1",
    )
    config_registry.register(
        configuration_id="cfg-demo",
        research_id="research-demo",
        access_policy="read-only",
        description="Demo config",
    )
    execution_registry.register(execution_id="exec-demo", configuration_id="cfg-demo")
    execution_registry.start("exec-demo")
    execution_registry.complete("exec-demo")
    result_registry.register(result_id="res-demo", execution_id="exec-demo")
    knowledge_registry.register(
        knowledge_id="knowledge-demo",
        result_id="res-demo",
        knowledge_type="MVP",
        description="Reusable insight generated from a demo result",
    )

    print(
        "Dataset -> Research Definition -> Research Configuration -> Research Execution -> Research Result -> Research Knowledge"
    )
    print(f"Knowledge registered: {knowledge_access.exists('knowledge-demo')}")
    print(f"Knowledge count: {len(knowledge_access.list())}")


if __name__ == "__main__":
    main()
