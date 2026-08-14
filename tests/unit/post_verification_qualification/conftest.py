from datetime import datetime, timezone
from decimal import Decimal

import pytest

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import verify_economic_reality
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime,
    ExternalEconomicAuthority,
    MonetaryCoverage,
    ObservedMonetaryAssertion,
    ObservedPositionAssertion,
    PositionCoverage,
    SupportingEconomicEvidence,
    observe_external_economic_reality,
)
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence,
    InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime,
    qualify_internal_economic_reality,
)
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


@pytest.fixture
def identities():
    return (
        InstrumentReference("FIGI", "AAPL"),
        InstrumentReference("FIGI", "MSFT"),
        InstrumentReference("FIGI", "TSLA"),
        CurrencyReference("USD"),
    )


@pytest.fixture
def make_verification():
    def make(*, internal_positions=(), external_positions=(), internal_money=(),
             external_money=(), covered_positions=None, covered_money=None):
        when = datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
        state = PortfolioState(
            positions=tuple(PortfolioPosition(i, Decimal(v)) for i, v in internal_positions),
            monetary_balances=tuple(MonetaryBalance(i, Decimal(v)) for i, v in internal_money),
        )
        internal = qualify_internal_economic_reality((InternalEconomicRealityEvidence(
            state, InternalEconomicRealityReferenceTime(when),
            InternalEconomicRealityProvenance("ledger"),
        ),))
        positions = tuple(ObservedPositionAssertion(i, Decimal(v)) for i, v in external_positions)
        money = tuple(ObservedMonetaryAssertion(i, Decimal(v)) for i, v in external_money)
        external = observe_external_economic_reality((SupportingEconomicEvidence(
            authority=ExternalEconomicAuthority("custodian"),
            reference_time=EconomicRealityReferenceTime(when),
            position_coverage=(
                PositionCoverage.complete()
                if not internal_positions and not external_positions and covered_positions is None
                else PositionCoverage.partial(
                    covered_positions if covered_positions is not None else (i for i, _ in external_positions)
                )
            ),
            monetary_coverage=MonetaryCoverage.partial(
                covered_money if covered_money is not None else (i for i, _ in external_money)
            ),
            observed_positions=positions,
            observed_monetary_balances=money,
        ),))
        return verify_economic_reality(internal, external)
    return make
