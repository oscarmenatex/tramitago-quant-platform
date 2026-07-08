"""Base provider contract for external market data.

Responsibility:
    Define the interface for obtaining raw external market data.

Inputs:
    Symbol, start date, end date, and interval.

Outputs:
    Raw provider data without normalization or internal validation.
"""

from abc import ABC, abstractmethod

import pandas as pd


class BaseProvider(ABC):
    """Contract for historical market data providers."""

    @abstractmethod
    def fetch(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Fetch raw historical data from an external provider."""
