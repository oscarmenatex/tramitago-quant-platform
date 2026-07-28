from datetime import datetime

from quant_platform.data.access import DatasetAccess
from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry, DatasetRecord


def valid_market_data() -> MarketData:
    return MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )


def test_access_existing_dataset() -> None:
    registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check([valid_market_data()])

    expected = registry.register(
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    access = DatasetAccess(registry)
    actual = access.get("dataset-001", "v1")

    assert isinstance(actual, DatasetRecord)
    assert actual == expected


def test_access_nonexistent_dataset_returns_none() -> None:
    registry = DatasetRegistry()
    access = DatasetAccess(registry)

    assert access.get("missing-dataset", "v1") is None


def test_access_preserves_quality_report_reference() -> None:
    registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check([valid_market_data()])

    expected = registry.register(
        dataset_id="dataset-002",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    access = DatasetAccess(registry)
    actual = access.get("dataset-002", "v1")

    assert actual is not None
    assert actual.quality_report_id == expected.quality_report_id
    assert actual.quality_report_id == quality_report.dataset_id


def test_access_does_not_modify_registered_record() -> None:
    registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check([valid_market_data()])

    expected = registry.register(
        dataset_id="dataset-003",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    access = DatasetAccess(registry)
    actual = access.get("dataset-003", "v1")

    assert actual == expected
    assert actual is expected
