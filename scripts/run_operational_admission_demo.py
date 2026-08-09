#!/usr/bin/env python3
"""Deterministic demonstration of the Operational Admission contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_admission import (
    OperationalAdmissionObservation,
    recognize_admission,
)
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


class ControlledAdmissionBoundary:
    """Demo-only boundary that normalizes evidence without deciding admission."""

    def observe(
        self, submission: OperationalSubmission
    ) -> OperationalAdmissionObservation:
        print("boundary received submission: yes")
        observation = OperationalAdmissionObservation(admitted=True)
        print("boundary produced normalized observation:", observation)
        return observation


def main() -> None:
    instrument = InstrumentReference("FIGI", "ADMISSION-DEMO")
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
    submission = OperationalSubmission(OperationalRequest(OperationalIntent(transition)))

    print("submission prepared:", submission)
    admission = recognize_admission(submission, ControlledAdmissionBoundary())
    print("Operational Admission recognized decision:", admission.decision.value)
    print("admission preserves submission:", admission.submission is submission)
    print("Operational Admission demo passed.")


if __name__ == "__main__":
    main()
