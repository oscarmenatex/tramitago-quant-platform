from decimal import Decimal

import pytest

from quant_platform.core import InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioPositionTransition,
    PortfolioTransition,
)
from tests.execution_planning_support import target_from_transition


@pytest.fixture
def operational_intent() -> OperationalIntent:
    bought = InstrumentReference("FIGI", "BUY-ME")
    sold = InstrumentReference("FIGI", "SELL-ME")
    current = PortfolioState(
        (
            PortfolioPosition(bought, Decimal("1")),
            PortfolioPosition(sold, Decimal("5")),
        )
    )
    target = PortfolioState(
        (
            PortfolioPosition(bought, Decimal("4")),
            PortfolioPosition(sold, Decimal("3")),
        )
    )
    transition = PortfolioTransition(
        current,
        target,
        (
            PortfolioPositionTransition(bought, Decimal("3")),
            PortfolioPositionTransition(sold, Decimal("-2")),
        ),
    )
    return OperationalIntent(target_from_transition(transition))
