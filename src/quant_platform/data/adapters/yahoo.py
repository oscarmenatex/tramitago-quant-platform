"""Yahoo Finance adapter for market data normalization.

Responsibility:
    Convert the DataFrame returned by yfinance into the MarketData contract.

Inputs:
    A pandas DataFrame with Yahoo Finance OHLCV columns and a symbol.

Outputs:
    list[MarketData] records independent from Yahoo Finance structures.
"""

from datetime import datetime

import pandas as pd

from quant_platform.data.adapters.base import BaseAdapter
from quant_platform.data.models import MarketData


class YahooAdapter(BaseAdapter):
    """Normalize Yahoo Finance historical OHLCV data."""

    REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")

    def to_market_data(self, raw_data: pd.DataFrame, symbol: str) -> list[MarketData]:
        """Convert a Yahoo Finance DataFrame into MarketData records."""
        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("YahooAdapter expects a pandas DataFrame.")

        frame = self._normalize_columns(raw_data)
        missing_columns = [
            column for column in self.REQUIRED_COLUMNS if column not in frame.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required Yahoo columns: {missing_columns}")

        records: list[MarketData] = []
        for timestamp, row in frame.iterrows():
            records.append(
                MarketData(
                    symbol=symbol,
                    timestamp=self._to_datetime(timestamp),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                )
            )

        return records

    def _normalize_columns(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with single-level Yahoo OHLCV columns."""
        frame = raw_data.copy()
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = frame.columns.get_level_values(0)
        return frame

    def _to_datetime(self, value: object) -> datetime:
        """Convert pandas-compatible timestamp values to datetime."""
        timestamp = pd.Timestamp(value)
        if pd.isna(timestamp):
            raise ValueError("Yahoo data contains an invalid timestamp.")
        return timestamp.to_pydatetime()
