"""Data Layer orchestration entry point.

Responsibility:
    Coordinate provider access, normalization, and validation.

Inputs:
    Symbol, date range, interval, and optional configured components.

Outputs:
    list[MarketData] records validated against the internal contract.
"""

from quant_platform.data.adapters import BaseAdapter, YahooAdapter
from quant_platform.data.factory import get_provider
from quant_platform.data.models import MarketData
from quant_platform.data.providers import BaseProvider
from quant_platform.data.validators import MarketDataValidator


class DataLoader:
    """Orchestrate the complete Data Layer MVP flow."""

    def __init__(
        self,
        data_provider: str = "yahoo",
        provider: BaseProvider | None = None,
        adapter: BaseAdapter | None = None,
        validator: MarketDataValidator | None = None,
    ) -> None:
        self.provider = (
            provider if provider is not None else get_provider(data_provider)
        )
        self.adapter = adapter if adapter is not None else YahooAdapter()
        self.validator = validator if validator is not None else MarketDataValidator()

    def get_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str = "1d",
    ) -> list[MarketData]:
        """Fetch, normalize, validate, and return historical market data."""
        raw_data = self.provider.fetch(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )
        market_data = self.adapter.to_market_data(raw_data, symbol)
        return self.validator.validate(market_data)
