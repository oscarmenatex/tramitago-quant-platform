from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from quant_platform.data.models import MarketData


def test_market_data_creation_and_immutability() -> None:
    record = MarketData(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2),
        open=100.0,
        high=105.0,
        low=99.0,
        close=104.0,
        volume=1_000_000.0,
    )

    assert record.symbol == "AAPL"
    assert isinstance(record.timestamp, datetime)
    assert record.close == 104.0

    with pytest.raises(FrozenInstanceError):
        record.close = 101.0
