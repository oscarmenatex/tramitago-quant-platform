"""Deterministic public demonstration for IT-044-001."""

from datetime import datetime, timezone
from decimal import Decimal

from quant_platform.core import InstrumentReference
from quant_platform.economic_reality_verification import EconomicRealityDimension, verify_economic_reality
from quant_platform.external_economic_observation import (
    EconomicRealityReferenceTime, ExternalEconomicAuthority, MonetaryCoverage,
    ObservedPositionAssertion, PositionCoverage, SupportingEconomicEvidence,
    observe_external_economic_reality,
)
from quant_platform.internal_economic_reality import (
    InternalEconomicRealityEvidence, InternalEconomicRealityProvenance,
    InternalEconomicRealityReferenceTime, qualify_internal_economic_reality,
)
from quant_platform.portfolio import PortfolioPosition, PortfolioState
from quant_platform.post_verification_qualification import (
    PostVerificationQualificationCondition as Condition,
    RequiredCorroborationRequirement, RequiredCorroborationScope,
    qualify_post_verification,
)


when = datetime(2026, 8, 12, 16, tzinfo=timezone.utc)
aapl = InstrumentReference("FIGI", "AAPL")
msft = InstrumentReference("FIGI", "MSFT")
tsla = InstrumentReference("FIGI", "TSLA")
state = PortfolioState(positions=(
    PortfolioPosition(aapl, Decimal(10)), PortfolioPosition(msft, Decimal(5)),
))
internal = qualify_internal_economic_reality((InternalEconomicRealityEvidence(
    state, InternalEconomicRealityReferenceTime(when),
    InternalEconomicRealityProvenance("ledger-demo"),
),))
external = observe_external_economic_reality((SupportingEconomicEvidence(
    authority=ExternalEconomicAuthority("custodian-demo"),
    reference_time=EconomicRealityReferenceTime(when),
    position_coverage=PositionCoverage.partial((aapl, msft)),
    monetary_coverage=MonetaryCoverage.partial(()),
    observed_positions=(
        ObservedPositionAssertion(aapl, Decimal(10)),
        ObservedPositionAssertion(msft, Decimal(6)),
    ),
    observed_monetary_balances=(),
),))
verification = verify_economic_reality(internal, external)


def scope_for(identity):
    return RequiredCorroborationScope((RequiredCorroborationRequirement(
        EconomicRealityDimension.POSITION, identity,
    ),))


conditions = {
    qualify_post_verification(verification, scope_for(aapl)).condition,
    qualify_post_verification(verification, scope_for(msft)).condition,
    qualify_post_verification(verification, scope_for(tsla)).condition,
}
assert conditions == {
    Condition.CORROBORATED, Condition.DIVERGENT, Condition.INSUFFICIENT_EVIDENCE,
}
print("EconomicRealityVerification + RequiredCorroborationScope")
print("PostVerificationQualification conditions:", sorted(x.value for x in conditions))
print("Post-Verification Qualification demo passed.")
