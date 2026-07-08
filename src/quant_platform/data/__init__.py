"""Data Layer public package.

Responsibility:
    Expose the initial Data Layer MVP components.

Inputs:
    Historical market data requests.

Outputs:
    Validated MarketData records through package modules.
"""

from quant_platform.data.loader import DataLoader

__all__ = ["DataLoader"]
