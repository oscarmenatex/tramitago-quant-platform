#!/usr/bin/env python3
"""Deterministic demonstration of the Operational Request public contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_request import OperationalRequest
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def main() -> None:
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
    transition = PortfolioTransition(
        current,
        target,
        (
            PortfolioPositionTransition(bought, Decimal("3")),
            PortfolioPositionTransition(sold, Decimal("-2")),
        ),
        (PortfolioMonetaryTransition(usd, Decimal("-20")),),
    )
    intent = OperationalIntent(transition)
    request = OperationalRequest(intent)

    assert request.operational_intent is intent
    assert request.operations == intent.operations
    print("origin:", request.operational_intent.semantic_identity)
    print(
        "operations:",
        [
            (
                operation.instrument.identification_value,
                operation.direction.value,
                str(operation.quantity),
            )
            for operation in request.operations
        ],
    )
    print("Operational Request demo passed.")


if __name__ == "__main__":
    main()
