"""Base adapter contract for market data normalization.

Responsibility:
    Define the interface for transforming external provider data.

Inputs:
    Raw provider payloads and a market symbol.

Outputs:
    A list of internal MarketData records.
"""

from abc import ABC, abstractmethod
from typing import Any

from quant_platform.data.models import MarketData


class BaseAdapter(ABC):
    """Contract for provider-specific market data adapters."""

    @abstractmethod
    def to_market_data(self, raw_data: Any, symbol: str) -> list[MarketData]:
        """Convert raw provider data into internal MarketData records."""
