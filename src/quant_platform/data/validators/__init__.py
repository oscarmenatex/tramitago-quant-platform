"""Data Layer validators.

Responsibility:
    Expose validation components for internal data contracts.

Inputs:
    Normalized MarketData records.

Outputs:
    Accepted MarketData records or validation errors.
"""

from quant_platform.data.validators.market_data_validator import MarketDataValidator

__all__ = ["MarketDataValidator"]
