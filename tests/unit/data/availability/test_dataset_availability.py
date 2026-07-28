from datetime import datetime

from quant_platform.data.access import DatasetAccess
from quant_platform.data.availability import DatasetAvailability, DatasetContentStore
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry


def test_availability_facade_resolves_exact_registered_version() -> None:
    content = [MarketData("AAPL", datetime(2024, 1, 2), 100, 105, 99, 104, 1_000_000)]
    registry = DatasetRegistry()
    report = MarketDataQualityChecker().check(content)
    record = registry.register("dataset-001", "AAPL", "v1", "synthetic", report)
    availability = DatasetAvailability(DatasetAccess(registry), DatasetContentStore())

    reference = availability.publish("dataset-001", "v1", content)

    assert reference is not None
    assert availability.resolve(reference) == (record, tuple(content))
