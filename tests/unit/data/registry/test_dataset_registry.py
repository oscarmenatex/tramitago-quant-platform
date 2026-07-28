from datetime import datetime

import pytest

from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry, DatasetRecord


def valid_record(
    symbol: str = "AAPL", timestamp: datetime = datetime(2024, 1, 2)
) -> MarketData:
    return MarketData(
        symbol=symbol,
        timestamp=timestamp,
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )


def test_register_valid_dataset() -> None:
    quality_report = MarketDataQualityChecker().check([valid_record()])
    registry = DatasetRegistry()

    record = registry.register(
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    assert isinstance(record, DatasetRecord)
    assert record.status == "REGISTERED"
    assert record.quality_report_id


def test_register_fail_quality_dataset_preserves_status() -> None:
    invalid_record = MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=98.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )
    quality_report = MarketDataQualityChecker().check([invalid_record])
    registry = DatasetRegistry()

    record = registry.register(
        dataset_id="dataset-002",
        name="AAPL invalid",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    assert record.status == "REGISTERED"
    assert record.quality_report_id
    assert quality_report.status == "FAIL"


def test_query_existing_dataset() -> None:
    registry = DatasetRegistry()
    quality_report = MarketDataQualityChecker().check([valid_record()])

    created = registry.register(
        dataset_id="dataset-003",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )

    queried = registry.get("dataset-003", "v1")

    assert queried == created


def test_register_without_dataset_id_raises() -> None:
    quality_report = MarketDataQualityChecker().check([valid_record()])
    registry = DatasetRegistry()

    with pytest.raises(ValueError, match="dataset_id"):
        registry.register(
            dataset_id="",
            name="AAPL sample",
            version="v1",
            source="synthetic",
            quality_report=quality_report,
        )
