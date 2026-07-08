"""MarketData internal contract.

Responsibility:
    Represent one provider-independent market observation.

Inputs:
    Symbol, timestamp, OHLC prices, and volume.

Outputs:
    An immutable MarketData value object.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketData:
    """Provider-independent market data observation."""

    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
