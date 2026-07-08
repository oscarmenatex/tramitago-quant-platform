import pandas as pd

from quant_platform.data.loader import DataLoader
from quant_platform.data.providers import BaseProvider


class StubProvider(BaseProvider):
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        assert symbol == "AAPL"
        assert start_date == "2024-01-01"
        assert end_date == "2025-01-01"
        assert interval == "1d"
        return pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [99.0],
                "Close": [104.0],
                "Volume": [1_000_000],
            },
            index=pd.to_datetime(["2024-01-02"]),
        )


def test_data_loader_returns_validated_market_data() -> None:
    records = DataLoader(provider=StubProvider()).get_historical_data(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2025-01-01",
    )

    assert len(records) == 1
    assert records[0].symbol == "AAPL"
    assert records[0].close == 104.0
