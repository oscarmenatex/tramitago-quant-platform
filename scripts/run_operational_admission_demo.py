#!/usr/bin/env python3
"""Deterministic demonstration of the Operational Admission contract."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_admission import (
    OperationalAdmissionDomainError,
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
from execution_demo_support import target_from_transition


class ControlledAdmissionBoundary:
    """Demo-only boundary that normalizes evidence without deciding admission."""

    def __init__(self, observation: OperationalAdmissionObservation) -> None:
        self.observation = observation

    def observe(
        self, submission: OperationalSubmission
    ) -> OperationalAdmissionObservation:
        print("boundary received submission: yes")
        print("boundary produced normalized observation:", self.observation)
        return self.observation


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
    submission = OperationalSubmission(
        OperationalRequest(OperationalIntent(target_from_transition(transition)))
    )

    print("submission prepared:", submission)
    for label, observation in (
        ("ADMITTED", OperationalAdmissionObservation(admitted=True)),
        ("REJECTED", OperationalAdmissionObservation(rejected=True)),
    ):
        admission = recognize_admission(
            submission,
            ControlledAdmissionBoundary(observation),
        )
        print(label, "recognized decision:", admission.decision.value)
        print(label, "preserves submission:", admission.submission is submission)

    try:
        recognize_admission(
            submission,
            ControlledAdmissionBoundary(OperationalAdmissionObservation()),
        )
    except OperationalAdmissionDomainError:
        print("insufficient evidence produced no admission: yes")
    else:
        raise AssertionError("Insufficient evidence must not produce an admission.")

    print("Operational Admission demo passed.")


if __name__ == "__main__":
    main()
