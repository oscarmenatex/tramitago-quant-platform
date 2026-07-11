from datetime import datetime
from math import inf
from pathlib import Path

import pytest

from quant_platform.data.models import MarketData
from quant_platform.data.quality import MarketDataQualityChecker


def valid_record(
    symbol: str = "AAPL",
    timestamp: datetime = datetime(2024, 1, 2),
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


def test_quality_checker_accepts_valid_market_data() -> None:
    report = MarketDataQualityChecker().check(
        [
            valid_record(timestamp=datetime(2024, 1, 2)),
            valid_record(timestamp=datetime(2024, 1, 3)),
        ]
    )

    assert report.status == "PASS"
    assert report.total_records == 2
    assert report.missing_records == 0
    assert report.duplicate_records == 0
    assert report.validation_errors == []


def test_quality_checker_fails_empty_dataset() -> None:
    report = MarketDataQualityChecker().check([])

    assert report.status == "FAIL"
    assert report.total_records == 0
    assert report.validation_errors


def test_quality_checker_detects_duplicate_records() -> None:
    record = valid_record()

    report = MarketDataQualityChecker().check([record, record])

    assert report.status == "FAIL"
    assert report.duplicate_records > 0
    assert report.validation_errors


def test_quality_checker_detects_invalid_ohlc_values() -> None:
    invalid_record = MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=98.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )

    report = MarketDataQualityChecker().check([invalid_record])

    assert report.status == "FAIL"
    assert report.validation_errors


def test_quality_checker_rejects_non_market_data_input() -> None:
    with pytest.raises(TypeError, match="MarketData"):
        MarketDataQualityChecker().check(["not", "market", "data"])


def test_quality_checker_detects_out_of_order_timestamps() -> None:
    report = MarketDataQualityChecker().check(
        [
            valid_record(timestamp=datetime(2024, 1, 3)),
            valid_record(timestamp=datetime(2024, 1, 2)),
        ]
    )

    assert report.status == "FAIL"
    assert report.validation_errors


def test_quality_checker_detects_invalid_numeric_values() -> None:
    invalid_record = MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=float("nan"),
        high=105.0,
        low=99.0,
        close=104.0,
        volume=inf,
    )

    report = MarketDataQualityChecker().check([invalid_record])

    assert report.status == "FAIL"
    assert report.validation_errors


def test_quality_checker_is_architecturally_independent() -> None:
    import quant_platform.data.quality.market_data_quality_checker as checker_module

    source_path = Path(checker_module.__file__)
    source = source_path.read_text(encoding="utf-8")
    forbidden_imports = (
        "pandas",
        "yfinance",
        "quant_platform.data.loader",
        "quant_platform.data.providers",
        "quant_platform.data.adapters",
    )

    for forbidden in forbidden_imports:
        assert forbidden not in source

    report = MarketDataQualityChecker().check([valid_record()])

    assert report.status == "PASS"
