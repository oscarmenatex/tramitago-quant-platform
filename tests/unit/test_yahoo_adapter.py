import pandas as pd

from quant_platform.data.adapters import YahooAdapter
from quant_platform.data.models import MarketData


def test_yahoo_adapter_converts_dataframe_to_market_data() -> None:
    raw_data = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
            "Volume": [1_000_000],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )

    records = YahooAdapter().to_market_data(raw_data, "AAPL")

    assert records == [
        MarketData(
            symbol="AAPL",
            timestamp=pd.Timestamp("2024-01-02").to_pydatetime(),
            open=100.0,
            high=105.0,
            low=99.0,
            close=104.0,
            volume=1_000_000.0,
        )
    ]
