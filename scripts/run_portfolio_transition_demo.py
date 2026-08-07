#!/usr/bin/env python3
"""Deterministic demonstration of the Portfolio Transition public contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    DuplicatePortfolioTransitionComponentError,
    InvalidPortfolioTransitionComponentError,
    InvalidPortfolioTransitionRelationError,
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


def main() -> None:
    a = InstrumentReference("FIGI", "A")
    b = InstrumentReference("FIGI", "B")
    usd = CurrencyReference("USD")
    current = PortfolioState(
        (PortfolioPosition(a, Decimal("1")), PortfolioPosition(b, Decimal("2"))),
        (MonetaryBalance(usd, Decimal("100")),),
    )
    target = PortfolioState(
        (PortfolioPosition(a, Decimal("3")), PortfolioPosition(b, Decimal("1"))),
        (MonetaryBalance(usd, Decimal("80")),),
    )
    a_change = PortfolioPositionTransition(a, Decimal("2"))
    b_change = PortfolioPositionTransition(b, Decimal("-1"))
    cash_change = PortfolioMonetaryTransition(usd, Decimal("-20"))
    transition = PortfolioTransition(
        current, target, (b_change, a_change), (cash_change,)
    )
    equivalent = PortfolioTransition(
        current,
        target,
        (
            PortfolioPositionTransition(a, Decimal("2.00")),
            PortfolioPositionTransition(b, Decimal("-1.0")),
        ),
        (PortfolioMonetaryTransition(usd, Decimal("-20.00")),),
    )

    assert transition.current_portfolio_state is current
    assert transition.target_portfolio_state is target
    assert transition == equivalent
    assert transition.semantic_identity == equivalent.semantic_identity
    print("canonical instruments:", [item.instrument.identification_value for item in transition.position_transitions])
    print("semantic_identity:", transition.semantic_identity)
    print("relation preserved:", transition.current_portfolio_state is current and transition.target_portfolio_state is target)

    checks = (
        (InvalidPortfolioTransitionRelationError, lambda: PortfolioTransition(current, current)),
        (DuplicatePortfolioTransitionComponentError, lambda: PortfolioTransition(current, target, (a_change, a_change), (cash_change,))),
        (InvalidPortfolioTransitionComponentError, lambda: PortfolioPositionTransition(a, Decimal("NaN"))),
    )
    for error_type, operation in checks:
        try:
            operation()
        except error_type:
            print("expected error:", error_type.__name__)
        else:
            raise AssertionError(f"Expected {error_type.__name__}")
    print("Portfolio Transition demo passed.")


if __name__ == "__main__":
    main()
