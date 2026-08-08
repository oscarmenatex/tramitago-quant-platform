#!/usr/bin/env python3
"""Deterministic demonstration of the Execution public contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent, OperationDirection
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

    assert intent.portfolio_transition is transition
    assert [operation.direction for operation in intent.operations] == [
        OperationDirection.BUY,
        OperationDirection.SELL,
    ]
    assert [operation.quantity for operation in intent.operations] == [
        Decimal("3"),
        Decimal("2"),
    ]
    assert len(intent.operations) == len(transition.position_transitions)
    assert intent == OperationalIntent(transition)
    print("origin:", intent.portfolio_transition.semantic_identity)
    print(
        "operations:",
        [
            (
                operation.instrument.identification_value,
                operation.direction.value,
                str(operation.quantity),
            )
            for operation in intent.operations
        ],
    )
    print("monetary operations: 0")
    print("semantic_identity:", intent.semantic_identity)
    print("Execution demo passed.")


if __name__ == "__main__":
    main()
