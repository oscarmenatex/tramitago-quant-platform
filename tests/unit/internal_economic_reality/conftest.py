from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence,
    InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime,
)
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


@pytest.fixture
def portfolio_state() -> PortfolioState:
    return PortfolioState(
        positions=(
            PortfolioPosition(InstrumentReference("FIGI", "IER-A"), Decimal("2")),
        ),
        monetary_balances=(MonetaryBalance(CurrencyReference("USD"), Decimal("50")),),
    )


@pytest.fixture
def reference_time() -> InternalEconomicRealityReferenceTime:
    return InternalEconomicRealityReferenceTime(
        datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
    )


@pytest.fixture
def evidence(portfolio_state, reference_time) -> InternalEconomicRealityEvidence:
    return InternalEconomicRealityEvidence(
        portfolio_state,
        reference_time,
        InternalEconomicRealityProvenance("internal-ledger"),
    )
