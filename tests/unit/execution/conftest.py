from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


@pytest.fixture
def transition() -> PortfolioTransition:
    bought = InstrumentReference("FIGI", "BUY-ME")
    sold = InstrumentReference("FIGI", "SELL-ME")
    usd = CurrencyReference("USD")
    current = PortfolioState(
        (
            PortfolioPosition(bought, Decimal("1")),
            PortfolioPosition(sold, Decimal("5")),
        ),
        (MonetaryBalance(usd, Decimal("100")),),
    )
    target = PortfolioState(
        (
            PortfolioPosition(bought, Decimal("4")),
            PortfolioPosition(sold, Decimal("3")),
        ),
        (MonetaryBalance(usd, Decimal("80")),),
    )
    return PortfolioTransition(
        current,
        target,
        (
            PortfolioPositionTransition(bought, Decimal("3")),
            PortfolioPositionTransition(sold, Decimal("-2")),
        ),
        (PortfolioMonetaryTransition(usd, Decimal("-20")),),
    )
