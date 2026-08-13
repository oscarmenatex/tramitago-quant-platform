"""Deterministic public demonstration for IT-043-001."""

from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.core import CurrencyReference, InstrumentReference
from quant_platform.economic_reality_verification import verify_economic_reality
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime, ExternalEconomicAuthority, MonetaryCoverage,
    ObservedMonetaryAssertion, ObservedPositionAssertion, PositionCoverage,
    SupportingEconomicEvidence, observe_external_economic_reality,
)
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence, InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime, qualify_internal_economic_reality,
)
from quant_platform.portfolio import MonetaryBalance, PortfolioPosition, PortfolioState


when = datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
aapl = InstrumentReference("FIGI", "AAPL")
msft = InstrumentReference("FIGI", "MSFT")
usd = CurrencyReference("USD")
state = PortfolioState(
    positions=(PortfolioPosition(aapl, Decimal(10)), PortfolioPosition(msft, Decimal(5))),
    monetary_balances=(MonetaryBalance(usd, Decimal(100)),),
)
internal = qualify_internal_economic_reality((InternalEconomicRealityEvidence(
    state, InternalEconomicRealityReferenceTime(when),
    InternalEconomicRealityProvenance("ledger-demo"),
),))
external = observe_external_economic_reality((SupportingEconomicEvidence(
    authority=ExternalEconomicAuthority("custodian-demo"),
    reference_time=EconomicRealityReferenceTime(when),
    position_coverage=PositionCoverage.partial((aapl,)),
    monetary_coverage=MonetaryCoverage.complete(),
    observed_positions=(ObservedPositionAssertion(aapl, Decimal(10)),),
    observed_monetary_balances=(ObservedMonetaryAssertion(usd, Decimal(90)),),
),))
verification = verify_economic_reality(internal, external)
assert {x.outcome.value for x in verification.position_results} == {"AGREEMENT", "NOT_COMPARABLE"}
assert {x.outcome.value for x in verification.monetary_results} == {"DISCREPANCY"}
print("Internal source:", verification.internal_reality)
print("External source:", verification.external_reality)
print("Position results:", verification.position_results)
print("Monetary results:", verification.monetary_results)
print("Economic Reality Verification demo passed.")
