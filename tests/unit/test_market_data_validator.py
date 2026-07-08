from datetime import datetime

import pytest

from quant_platform.data.models import MarketData
from quant_platform.data.validators import MarketDataValidator


def valid_record() -> MarketData:
    return MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )


def test_validator_accepts_valid_market_data() -> None:
    records = [valid_record()]

    assert MarketDataValidator().validate(records) == records


def test_validator_rejects_invalid_ohlc_values() -> None:
    invalid_record = MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=98.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )

    with pytest.raises(ValueError, match="inconsistent OHLC"):
        MarketDataValidator().validate([invalid_record])
