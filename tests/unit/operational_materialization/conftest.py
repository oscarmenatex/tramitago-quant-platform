from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.execution import OperationalIntent
from quant_platform.operational_admission import AdmissionDecision, OperationalAdmission
from quant_platform.operational_request import OperationalRequest
from quant_platform.operational_submission import OperationalSubmission
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState
from quant_platform.portfolio_transition import (
    PortfolioMonetaryTransition,
    PortfolioPositionTransition,
    PortfolioTransition,
)
from tests.execution_planning_support import target_from_transition


@pytest.fixture
def admission() -> OperationalAdmission:
    instrument = InstrumentReference("FIGI", "MATERIALIZATION-TEST")
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
    return OperationalAdmission(submission, AdmissionDecision.ADMITTED)
