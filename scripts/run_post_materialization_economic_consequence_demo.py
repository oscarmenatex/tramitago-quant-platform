#!/usr/bin/env python3
"""Deterministic public demo of post-materialization economic consequence."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import InvestmentOperation, OperationDirection
from quant_platform.operational_materialization import OperationalMaterialization
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.post_materialization_economic_consequence import (
    derive_post_materialization_consequence,
)


def main() -> None:
    instrument = InstrumentReference("FIGI", "CONSEQUENCE-DEMO")
    usd = CurrencyReference("USD")
    previous = PortfolioState(
        (PortfolioPosition(instrument, Decimal("10")),),
        (MonetaryBalance(usd, Decimal("1000")),),
    )
    source = OperationalMaterialization(
        InvestmentOperation(instrument, OperationDirection.BUY, Decimal("100")),
        Decimal("3"),
        Decimal("25"),
        usd,
    )
    consequence = derive_post_materialization_consequence(previous, [source])

    print("S0:", consequence.previous_portfolio_state)
    print("source materialization:", consequence.source_materializations)
    print("position consequence: +3")
    print("gross monetary consequence: -(3 * 25) = -75 USD")
    print("S1:", consequence.resulting_portfolio_state)
    print("No settlement or P&L is asserted.")

    assert consequence.resulting_portfolio_state.positions[0].quantity == Decimal("13")
    assert consequence.resulting_portfolio_state.monetary_balances[0].amount == Decimal("925")
    print("Post-Materialization Economic Consequence demo passed.")


if __name__ == "__main__":
    main()
