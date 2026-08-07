from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


@pytest.fixture
def instrument() -> InstrumentReference:
    return InstrumentReference("FIGI", "A")


@pytest.fixture
def currency() -> CurrencyReference:
    return CurrencyReference("USD")


@pytest.fixture
def current_state(
    instrument: InstrumentReference, currency: CurrencyReference
) -> PortfolioState:
    return PortfolioState(
        (PortfolioPosition(instrument, Decimal("1")),),
        (MonetaryBalance(currency, Decimal("100")),),
    )


@pytest.fixture
def target_state(
    instrument: InstrumentReference, currency: CurrencyReference
) -> PortfolioState:
    return PortfolioState(
        (PortfolioPosition(instrument, Decimal("3")),),
        (MonetaryBalance(currency, Decimal("80")),),
    )
