"""External market data providers.

Responsibility:
    Expose provider contracts and concrete provider implementations.

Inputs:
    Historical market data requests.

Outputs:
    Raw provider payloads.
"""

from quant_platform.data.providers.base import BaseProvider
from quant_platform.data.providers.yahoo import YahooFinanceProvider

__all__ = ["BaseProvider", "YahooFinanceProvider"]
