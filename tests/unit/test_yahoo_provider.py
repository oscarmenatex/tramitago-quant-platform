import pandas as pd

from quant_platform.data.providers.yahoo import YahooFinanceProvider


def test_yahoo_provider_returns_raw_download_dataframe(monkeypatch) -> None:
    expected = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [105.0],
            "Low": [99.0],
            "Close": [104.0],
            "Volume": [1_000_000],
        },
        index=pd.to_datetime(["2024-01-02"]),
    )

    def fake_download(**kwargs):
        assert kwargs["tickers"] == "AAPL"
        assert kwargs["start"] == "2024-01-01"
        assert kwargs["end"] == "2025-01-01"
        assert kwargs["interval"] == "1d"
        return expected

    monkeypatch.setattr(
        "quant_platform.data.providers.yahoo.yf.download", fake_download
    )

    result = YahooFinanceProvider().fetch(
        symbol="AAPL",
        start_date="2024-01-01",
        end_date="2025-01-01",
        interval="1d",
    )

    assert result is expected
