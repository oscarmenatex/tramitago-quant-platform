#!/usr/bin/env python3
"""Deterministic demonstration of Operational Materialization recognition."""

from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_materialization import (
    OperationalMaterializationObservation,
    recognize_materialization,
)
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)


class ControlledMaterializationBoundary:
    """Demo-only normalized evidence source with no productive infrastructure."""

    def observe(
        self, admission: OperationalAdmission
    ) -> OperationalMaterializationObservation:
        operation = admission.submission.operational_request.operations[0]
        observation = OperationalMaterializationObservation(
            operation=operation,
            quantity=Decimal("0.75"),
            price=Decimal("25.40"),
            currency=CurrencyReference("USD"),
        )
        print("boundary produced Observation:", observation)
        return observation


def main() -> None:
    instrument = InstrumentReference("FIGI", "MATERIALIZATION-DEMO")
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
    intent = OperationalIntent(transition)
    submission = OperationalSubmission(OperationalRequest(intent))
    admission = OperationalAdmission(submission, AdmissionDecision.ADMITTED)

    print("InvestmentOperation:", intent.operations[0])
    print("OperationalAdmission:", admission.decision.value)
    materialization = recognize_materialization(
        admission, ControlledMaterializationBoundary()
    )
    assert materialization is not None
    print("recognized Materialization:", materialization)
    print("operation:", materialization.operation)
    print("quantity:", materialization.quantity)
    print("price:", materialization.price)
    print("currency:", materialization.currency.currency_code)
    print("Observation and Materialization are distinct contracts: yes")
    print("productive infrastructure used: no")
    print("Operational Materialization demo passed.")


if __name__ == "__main__":
    main()
