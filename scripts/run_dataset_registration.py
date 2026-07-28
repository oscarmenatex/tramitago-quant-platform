"""Dataset Registration MVP demonstration."""

from datetime import datetime

from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker
from quant_platform.data.registry import DatasetRegistry


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
        ),
    ]


def main() -> None:
    checker = MarketDataQualityChecker()
    quality_report = checker.check(build_valid_market_data())
    registry = DatasetRegistry()
    record = registry.register(
        dataset_id="dataset-001",
        name="AAPL sample",
        version="v1",
        source="synthetic",
        quality_report=quality_report,
    )
    print(f"dataset_id: {record.dataset_id}")
    print(f"name: {record.name}")
    print(f"version: {record.version}")
    print(f"source: {record.source}")
    print(f"status: {record.status}")
    print(f"quality_report_id: {record.quality_report_id}")


if __name__ == "__main__":
    main()
