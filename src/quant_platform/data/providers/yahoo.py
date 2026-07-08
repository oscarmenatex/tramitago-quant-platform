"""Yahoo Finance market data provider.

Responsibility:
    Obtain raw historical market data from yfinance.

Inputs:
    Symbol, start date, end date, and interval.

Outputs:
    Raw pandas DataFrame returned by yfinance.
"""

import pandas as pd
import yfinance as yf

from quant_platform.data.providers.base import BaseProvider


class YahooFinanceProvider(BaseProvider):
    """Fetch historical data from Yahoo Finance through yfinance."""

    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Return raw Yahoo Finance historical data without transformation."""
        return yf.download(
            tickers=symbol,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False,
            auto_adjust=False,
        )
