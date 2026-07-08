"""Adapters for external market data formats.

Responsibility:
    Convert provider-specific structures into internal MarketData records.

Inputs:
    Raw provider payloads.

Outputs:
    list[MarketData] values.
"""

from quant_platform.data.adapters.base import BaseAdapter
from quant_platform.data.adapters.yahoo import YahooAdapter

__all__ = ["BaseAdapter", "YahooAdapter"]
