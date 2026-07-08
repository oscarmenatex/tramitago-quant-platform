"""Internal data contracts for the Data Layer.

Responsibility:
    Expose provider-independent data models.

Inputs:
    Normalized market observations.

Outputs:
    Stable internal contracts consumed by the platform.
"""

from quant_platform.data.models.market_data import MarketData

__all__ = ["MarketData"]
