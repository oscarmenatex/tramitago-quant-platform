#!/usr/bin/env python3
"""Deterministic demonstration of the Operational Submission contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission, submit
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)
from execution_demo_support import target_from_transition


class ControlledPresentationBoundary:
    """Demo-only boundary with no network or external infrastructure."""

    def __init__(self) -> None:
        self.presented_request: OperationalRequest | None = None

    def present(self, operational_request: OperationalRequest) -> None:
        print("presenting operations:", operational_request.operations)
        self.presented_request = operational_request
        print("presentation completed: yes")


def main() -> None:
    instrument = InstrumentReference("FIGI", "SUBMIT-DEMO")
    currency = CurrencyReference("USD")
    current = PortfolioState(
        (PortfolioPosition(instrument, Decimal("1")),),
        (MonetaryBalance(currency, Decimal("100")),),
    )
    target = PortfolioState(
        (PortfolioPosition(instrument, Decimal("3")),),
        (MonetaryBalance(currency, Decimal("80")),),
    )
    transition = PortfolioTransition(
        current,
        target,
        (PortfolioPositionTransition(instrument, Decimal("2")),),
        (PortfolioMonetaryTransition(currency, Decimal("-20")),),
    )
    request = OperationalRequest(OperationalIntent(target_from_transition(transition)))
    boundary = ControlledPresentationBoundary()

    submission = submit(request, boundary)

    assert boundary.presented_request is request
    assert isinstance(submission, OperationalSubmission)
    assert submission.operational_request is request
    print("submission produced: yes")
    print("submission references presented request: yes")
    print("Operational Submission demo passed.")


if __name__ == "__main__":
    main()
