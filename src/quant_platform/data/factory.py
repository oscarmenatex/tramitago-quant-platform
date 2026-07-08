"""Provider factory for the Data Layer MVP.

Responsibility:
    Select the configured external data provider.

Inputs:
    Provider name.

Outputs:
    A provider implementing BaseProvider.
"""

from quant_platform.data.providers import BaseProvider, YahooFinanceProvider


def get_provider(name: str) -> BaseProvider:
    """Return the configured market data provider."""
    normalized_name = name.strip().lower()
    if normalized_name == "yahoo":
        return YahooFinanceProvider()

    raise ValueError(f"Unknown data provider: {name}")
